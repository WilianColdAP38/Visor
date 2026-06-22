from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from db import SessionDep
from models import (
    Usuarios,
    Pines,
    Comentarios,
    ComentariosCreate,
    ComentariosPublic,
)
from app.auth import get_current_user


router = APIRouter(prefix="/pines", tags=["Comentarios"])


# helper privado, evita repetir la misma validacion en los dos endpoints
def _get_pin_activo(pin_id: int, session: SessionDep) -> Pines:
    pin = session.get(Pines, pin_id)

    # soft delete tambien cuenta como no encontrado, asi no se filtra que el pin existio
    if not pin or pin.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El pin no fue encontrado",
        )

    return pin


@router.get(
    "/{pin_id}/comentarios",
    response_model=list[ComentariosPublic],
)
def listar_comentarios(pin_id: int, session: SessionDep):
    # se valida primero que el pin exista, evita devolver lista vacia confundiendo al cliente
    _get_pin_activo(pin_id, session)

    # solo los comentarios vivos, los soft deleted no salen
    comentarios = session.exec(
        select(Comentarios)
        .where(Comentarios.pin_id == pin_id)
        .where(Comentarios.deleted_at == None)  # noqa: E711
        .order_by(Comentarios.created_at.desc())
    ).all()

    return comentarios


@router.post(
    "/{pin_id}/comentarios",
    response_model=ComentariosPublic,
    status_code=status.HTTP_201_CREATED,
)
def crear_comentario(
    pin_id: int,
    datos: ComentariosCreate,
    session: SessionDep,
    usuario_actual: Usuarios = Depends(get_current_user),
):
    # el pin debe existir y estar activo
    _get_pin_activo(pin_id, session)

    # el contenido se limpia de espacios sobrantes antes de guardar
    contenido = datos.contenido.strip()

    if not contenido:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El comentario no puede estar vacio",
        )

    # el autor sale del token, NUNCA del body, asi nadie puede suplantar a otro usuario
    comentario = Comentarios(
        contenido=contenido,
        pin_id=pin_id,
        usuario_id=usuario_actual.id,
    )

    session.add(comentario)
    session.commit()
    session.refresh(comentario)

    return comentario