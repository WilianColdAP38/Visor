import io
import uuid
from random import sample

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import func, select

from db import SessionDep
from app.config import settings
from models import (
    Usuarios,
    Pines,
    PinesPublic,
    Likes,
    Comentarios,
)
from app.auth import get_current_user, get_optional_user


router = APIRouter(prefix="/pines", tags=["Pines"])


# cliente boto3 unico, se crea una sola vez al importar el modulo con las claves del .env
# usa la identidad wilian-visor-app-s3, el unico principal con permiso sobre el bucket
s3 = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)


# control de publicacion, mecanismo etico 2, solo imagenes y con tope de peso
TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}
TAMANO_MAX = 5 * 1024 * 1024  # 5 MB en bytes


# tiempo de vida de cada url firmada, una hora basta para cargar el feed
PRESIGNED_EXPIRA = 3600


def _firmar_source(source: str) -> str:
    # si por alguna razon el source ya es una url completa lo dejo igual, no lo firmo
    if source.startswith("http"):
        return source

    # source es una clave del bucket privado, genero una url temporal firmada
    # asi el navegador puede ver la imagen sin que el bucket sea publico
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": source},
        ExpiresIn=PRESIGNED_EXPIRA,
    )


# helper privado, centraliza la condicion de pin visible para no repetirla
def _pin_visible_filter():
    # solo pines no borrados y publicos, asi la privacidad se respeta en todos los GET
    return (Pines.deleted_at == None) & (Pines.es_publico == True)  # noqa: E712


def _serializar_pin(pin: Pines, session: SessionDep, usuario_actual: Usuarios | None) -> dict:
    # cuenta likes con una subquery, evita traer toda la lista en memoria
    likes_count = session.exec(
        select(func.count(Likes.id)).where(Likes.pin_id == pin.id)
    ).one()

    # cuenta comentarios del pin, el schema PinesPublic lo requiere
    comentarios_count = session.exec(
        select(func.count(Comentarios.id)).where(Comentarios.pin_id == pin.id)
    ).one()

    # si hay usuario logueado se revisa si el ya dio like, asi el front pinta el corazon lleno
    dio_like = False
    if usuario_actual:
        like_existente = session.exec(
            select(Likes).where(
                (Likes.pin_id == pin.id) & (Likes.usuario_id == usuario_actual.id)
            )
        ).first()
        dio_like = like_existente is not None

    # se devuelve un dict porque PinesPublic tiene campos calculados que no estan en la tabla
    return {
        "id": pin.id,
        "titulo": pin.titulo,
        "descripcion": pin.descripcion,
        "tags": pin.tags,
        "categoria": pin.categoria,
        # firmo la clave en runtime, el navegador recibe una url temporal no la clave cruda
        "source": _firmar_source(pin.source),
        "es_publico": pin.es_publico,
        "created_at": pin.created_at,
        "autor": pin.autor,
        "likes_count": likes_count,
        "comentarios_count": comentarios_count,
        "dio_like": dio_like,
    }


@router.get("/", response_model=list[PinesPublic])
def listar_pines(
    session: SessionDep,
    categoria: str | None = None,
    buscar: str | None = None,
    usuario: str | None = None,
    usuario_actual: Usuarios | None = Depends(get_optional_user),
):
    # se arma la query base con el filtro de visibilidad siempre activo
    query = select(Pines).where(_pin_visible_filter())

    if categoria:
        query = query.where(Pines.categoria == categoria)

    if buscar:
        # busqueda case insensitive en titulo, descripcion y tags
        like_pattern = f"%{buscar.lower()}%"
        query = query.where(
            func.lower(Pines.titulo).like(like_pattern)
            | func.lower(Pines.descripcion).like(like_pattern)
            | func.lower(Pines.tags).like(like_pattern)
        )

    if usuario:
        # filtra por handle del autor, sirve para el feed del perfil
        usuario_db = session.exec(
            select(Usuarios).where(Usuarios.usuario == usuario.lower())
        ).first()
        if not usuario_db:
            return []
        query = query.where(Pines.usuario_id == usuario_db.id)

    pines = session.exec(query).all()

    # si no hay filtros se mezcla aleatorio, asi el feed nunca se ve igual dos veces
    if not categoria and not buscar and not usuario and len(pines) > 1:
        pines = sample(pines, len(pines))

    return [_serializar_pin(p, session, usuario_actual) for p in pines]


@router.get("/{pin_id}", response_model=PinesPublic)
def obtener_pin(
    pin_id: int,
    session: SessionDep,
    usuario_actual: Usuarios | None = Depends(get_optional_user),
):
    pin = session.get(Pines, pin_id)

    # 404 cubre tres casos, no existe, esta soft deleted, o es privado de otro usuario
    if not pin or pin.deleted_at is not None or not pin.es_publico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El pin no fue encontrado",
        )

    return _serializar_pin(pin, session, usuario_actual)


@router.post("/", response_model=PinesPublic, status_code=status.HTTP_201_CREATED)
def crear_pin(
    session: SessionDep,
    # cada campo va como Form aplanado, asi swagger arma bien el multipart junto al archivo
    # las validaciones de largo son las mismas que tenia el schema PinesCreate
    titulo: str = Form(min_length=3, max_length=150),
    categoria: str = Form(min_length=2, max_length=50),
    descripcion: str | None = Form(default=None, max_length=500),
    tags: str | None = Form(default=None, max_length=300),
    es_publico: bool = Form(default=True),
    imagen: UploadFile = File(),
    # sin sesion no hay subida, mecanismo etico 1, control de acceso
    usuario_actual: Usuarios = Depends(get_current_user),
):
    # control de publicacion, rechazo cualquier cosa que no sea imagen permitida
    if imagen.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no permitido, solo se aceptan jpg, png o webp",
        )

    # leo el archivo una vez para poder validar el peso antes de subir nada
    contenido = imagen.file.read()
    if len(contenido) > TAMANO_MAX:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen supera el limite de 5 MB",
        )

    # la clave namespacea por uuid, asi dos archivos con igual nombre nunca chocan
    s3_key = f"pines/{uuid.uuid4()}-{imagen.filename}"

    # subo primero a S3, si esto falla no quiero un pin huerfano en la base
    try:
        s3.upload_fileobj(
            io.BytesIO(contenido),
            settings.S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": imagen.content_type or "image/jpeg"},
        )
    except Exception as e:
        # diagnostico temporal, muestro el error real de aws para saber que falla
        print("ERROR S3:", repr(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error S3: {repr(e)}",
        )

    # en la base guardo solo la clave del objeto, nunca una url, el GET la firma despues
    pin = Pines(
        titulo=titulo,
        descripcion=descripcion,
        tags=tags,
        categoria=categoria,
        es_publico=es_publico,
        source=s3_key,
        usuario_id=usuario_actual.id,
    )
    session.add(pin)
    session.commit()
    session.refresh(pin)

    return _serializar_pin(pin, session, usuario_actual)