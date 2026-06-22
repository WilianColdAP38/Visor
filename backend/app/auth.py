from datetime import datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import select

from app.config import settings
from db import SessionDep
from models import Usuarios, Rol


# ==============================
# CONFIGURACION DE HASHING Y JWT
# ==============================

# uso bcrypt directamente porque passlib tiene un bug de compatibilidad con las versiones recientes de bcrypt
# bcrypt es estandar de facto para passwords, genera salt unico por cada hash automaticamente
# si en el futuro quisiera cambiar a argon2 solo tocaria estas dos funciones de hash

# este esquema le dice a fastapi de donde sacar el token, el tokenUrl es la ruta que usa el boton Authorize de swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/token")


# ==============================
# HASH DE PASSWORDS
# ==============================

# bcrypt tiene un limite duro de 72 bytes en el input, recorto antes de hashear para evitar errores
# en la practica nadie usa passwords de mas de 72 caracteres, pero asi me curo en salud
def _truncate(password: str) -> bytes:
    return password.encode("utf-8")[:72]


# hashea el password antes de guardarlo, bcrypt genera salt unico por cada llamada
def hash_password(password: str) -> str:
    hash_bytes = bcrypt.hashpw(_truncate(password), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


# verifica el password plano contra el hash guardado en la BD
def verify_password(plano: str, hash_guardado: str) -> bool:
    return bcrypt.checkpw(_truncate(plano), hash_guardado.encode("utf-8"))


# ==============================
# CREACION Y VALIDACION DE TOKENS
# ==============================

# firma un jwt con el id del usuario, asi cualquier request puede identificar quien es sin guardar sesion en el servidor
def create_access_token(usuario_id: int) -> str:
    expira_en = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(usuario_id),  # subject, identifica al usuario en el token (jwt requiere string)
        "exp": expira_en,        # expiration, jose valida automaticamente que no este vencido
        "iat": datetime.utcnow(),  # issued at, util para auditoria
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# decodifica el token y devuelve el id del usuario, si falla algo devuelve None
def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        subject = payload.get("sub")
        # el sub se firmo como string pero el id es int, se convierte de regreso
        return int(subject) if subject else None
    except (JWTError, ValueError, TypeError):
        # cualquier error (firma invalida, expirado, malformado, sub corrupto) cae aqui
        # el server NUNCA debe caer por un token raro del cliente
        return None

# ==============================
# DEPENDENCIAS PARA LOS ROUTERS
# ==============================

# obtiene el usuario actual a partir del token del header Authorization
# si el token no existe, esta vencido, o el usuario fue borrado, devuelve 401
def get_current_user(
    session: SessionDep,
    token: str = Depends(oauth2_scheme),
) -> Usuarios:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas o sesion expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )

    usuario_id = decode_token(token)
    if usuario_id is None:
        raise credenciales_invalidas

    # se valida que el usuario aun exista y no este borrado, asi un token de un usuario eliminado deja de funcionar
    query = select(Usuarios).where(
        Usuarios.id == usuario_id,
        Usuarios.deleted_at.is_(None),
    )
    usuario = session.exec(query).first()

    if usuario is None:
        raise credenciales_invalidas

    return usuario


# version opcional, para endpoints publicos que se enriquecen si hay sesion pero funcionan sin ella
# por ejemplo el feed: si el usuario esta logueado, marca cuales pines ya le dio like
def get_optional_user(
    session: SessionDep,
    token: str | None = Depends(OAuth2PasswordBearer(tokenUrl="/usuarios/token", auto_error=False)),
) -> Usuarios | None:
    if token is None:
        return None

    usuario_id = decode_token(token)
    if usuario_id is None:
        return None

    query = select(Usuarios).where(
        Usuarios.id == usuario_id,
        Usuarios.deleted_at.is_(None),
    )
    return session.exec(query).first()


# protege endpoints administrativos, requiere que el usuario tenga rol ADMIN
def require_admin(usuario: Usuarios = Depends(get_current_user)) -> Usuarios:
    if usuario.rol != Rol.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta accion requiere permisos de administrador",
        )
    return usuario