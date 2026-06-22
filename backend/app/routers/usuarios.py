from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from db import SessionDep
from models import (
    Usuarios,
    UsuariosCreate,
    UsuariosLogin,
    UsuariosPublic,
    TokenResponse,
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# helper privado, centraliza la validacion de credenciales para no repetirla
# lo usan el login real (json, lo llama el frontend) y el /token de swagger (formulario)
def _autenticar_usuario(email: str, password: str, session: SessionDep) -> Usuarios:
    email = email.lower().strip()

    usuario_db = session.exec(
        select(Usuarios).where(Usuarios.email == email)
    ).first()

    # mensaje generico para no filtrar si el email existe o no, defensa contra enumeracion
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas",
    )

    if not usuario_db:
        raise credenciales_invalidas

    # si la cuenta esta dada de baja con soft delete tampoco deja entrar
    if usuario_db.deleted_at is not None:
        raise credenciales_invalidas

    if not verify_password(password, usuario_db.password):
        raise credenciales_invalidas

    return usuario_db


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(datos: UsuariosCreate, session: SessionDep):
    # normaliza para que no se cuelen duplicados por mayusculas o espacios
    email = datos.email.lower().strip()
    usuario = datos.usuario.lower().strip()

    # revisa si el email o el usuario ya estan tomados, una sola query
    existente = session.exec(
        select(Usuarios).where(
            (Usuarios.email == email) | (Usuarios.usuario == usuario)
        )
    ).first()

    if existente:
        # 409 conflict, es el codigo correcto cuando el recurso choca con uno existente
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email o el nombre de usuario ya estan registrados",
        )

    # crea el usuario con la password ya hasheada, nunca se guarda en claro
    nuevo = Usuarios(
        nombre=datos.nombre.strip(),
        usuario=usuario,
        email=email,
        password=hash_password(datos.password),
    )

    session.add(nuevo)
    session.commit()
    session.refresh(nuevo)

    # firma el token con el id como sub, asi el get_current_user puede recuperar al usuario
    token = create_access_token(nuevo.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UsuariosPublic.model_validate(nuevo),
    )


@router.post("/login", response_model=TokenResponse)
def login(datos: UsuariosLogin, session: SessionDep):
    # login real de la aplicacion, recibe json con email y password, lo consume el frontend
    usuario_db = _autenticar_usuario(datos.email, datos.password, session)
    token = create_access_token(usuario_db.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UsuariosPublic.model_validate(usuario_db),
    )


@router.post("/token", response_model=TokenResponse)
def token_swagger(
    session: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    # endpoint dedicado solo a la documentacion interactiva de swagger
    # el boton Authorize manda un formulario oauth2 (username/password), no json,
    # por eso necesita su propia ruta separada del login real
    # el campo username del estandar oauth2 lo trato como el email del usuario
    usuario_db = _autenticar_usuario(form_data.username, form_data.password, session)
    token = create_access_token(usuario_db.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UsuariosPublic.model_validate(usuario_db),
    )


@router.get("/me", response_model=UsuariosPublic)
def get_me(usuario_actual: Usuarios = Depends(get_current_user)):
    # endpoint para que el front recupere los datos del usuario logueado al refrescar la pagina
    return usuario_actual