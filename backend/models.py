from datetime import datetime
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import UniqueConstraint  


# ==============================
# ENUMS (valores controlados)
# ==============================

# roles del sistema, mejor enum que strings sueltos para evitar typos
class Rol(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


# ==============================
# TABLAS (table=True, viven en la BD)
# ==============================

# tabla de usuarios, el password siempre hasheado con bcrypt
class Usuarios(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    usuario: str = Field(unique=True, index=True)  # unique a nivel BD, index acelera el login
    email: EmailStr = Field(unique=True, index=True)
    password: str  # hash bcrypt de 60 chars, jamas texto plano
    bio: str | None = None  # descripcion corta del perfil, opcional
    foto_perfil: str | None = None  # url al avatar en s3, opcional
    rol: Rol = Field(default=Rol.USER)  # por defecto todos son USER, el primero se hace admin en seed

    # auditoria, util para defensa y para ordenar usuarios por antiguedad
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # soft delete, en vez de borrar de la BD se marca con fecha
    deleted_at: datetime | None = None

    # relaciones, un usuario puede tener muchos pines, comentarios y likes
    pines: list["Pines"] = Relationship(back_populates="autor")
    comentarios: list["Comentarios"] = Relationship(back_populates="autor")
    likes: list["Likes"] = Relationship(back_populates="usuario")


# tabla principal del feed, source es la url publica del archivo en s3
class Pines(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titulo: str
    descripcion: str | None = None
    tags: str | None = None  # csv simple, ej "viaje,playa,ecuador"
    categoria: str = Field(index=True)  # index porque el feed filtra muchisimo por categoria
    source: str  # url completa del archivo en s3
    es_publico: bool = True  # mecanismo etico, si es false el pin no sale en el feed publico

    # fk al autor del pin
    usuario_id: int = Field(foreign_key="usuarios.id", index=True)

    # auditoria
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)  # index para ordenar feed por recencia
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None  # soft delete

    # relaciones
    autor: Usuarios | None = Relationship(back_populates="pines")
    comentarios: list["Comentarios"] = Relationship(back_populates="pin")
    likes: list["Likes"] = Relationship(back_populates="pin")


# comentarios anidados a cada pin, sin respuestas a comentarios para mantener simple el alcance
class Comentarios(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    contenido: str
    pin_id: int = Field(foreign_key="pines.id", index=True)
    usuario_id: int = Field(foreign_key="usuarios.id", index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None  # soft delete, asi el moderador puede ocultar sin perder evidencia

    # relaciones
    pin: Pines | None = Relationship(back_populates="comentarios")
    autor: Usuarios | None = Relationship(back_populates="comentarios")


# tabla pivot de likes, cada like es una fila que une un usuario y un pin
# se modela asi y no como contador en Pines porque permite saber QUIEN dio like
class Likes(SQLModel, table=True):
    # un usuario solo puede dar UN like a cada pin, restriccion a nivel BD
    __table_args__ = (
        UniqueConstraint("usuario_id", "pin_id", name="uq_likes_usuario_pin"),
    )

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id", index=True)
    pin_id: int = Field(foreign_key="pines.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # relaciones
    usuario: Usuarios | None = Relationship(back_populates="likes")
    pin: Pines | None = Relationship(back_populates="likes")


# ==============================
# ESQUEMAS DE ENTRADA (lo que llega en el body)
# ==============================

class UsuariosCreate(SQLModel):
    nombre: str = Field(min_length=3, max_length=100)
    usuario: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)  # se hashea en el router, nunca aqui
    bio: str | None = Field(default=None, max_length=300)


class UsuariosLogin(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UsuariosUpdate(SQLModel):
    # solo permite editar campos no criticos, el email y password tienen flujos propios
    nombre: str | None = Field(default=None, min_length=3, max_length=100)
    bio: str | None = Field(default=None, max_length=300)
    foto_perfil: str | None = None


class PinesCreate(SQLModel):
    titulo: str = Field(min_length=3, max_length=150)
    descripcion: str | None = Field(default=None, max_length=500)
    tags: str | None = Field(default=None, max_length=300)
    categoria: str = Field(min_length=2, max_length=50)
    es_publico: bool = True


class ComentariosCreate(SQLModel):
    contenido: str = Field(min_length=1, max_length=300)


# ==============================
# ESQUEMAS DE SALIDA (lo que devuelve la api)
# ==============================

# nunca incluye password, el hash no sale del backend bajo ninguna circunstancia
class UsuariosPublic(SQLModel):
    id: int
    nombre: str
    usuario: str
    email: EmailStr
    bio: str | None
    foto_perfil: str | None
    rol: Rol
    created_at: datetime


# autor anidado, sale del Relationship "autor" de la tabla Comentarios
class ComentariosPublic(SQLModel):
    id: int
    contenido: str
    pin_id: int
    created_at: datetime
    autor: UsuariosPublic


# autor anidado y campos calculados en runtime, no son columnas de la tabla
class PinesPublic(SQLModel):
    id: int
    titulo: str
    descripcion: str | None
    tags: str | None
    categoria: str
    source: str
    es_publico: bool
    created_at: datetime
    autor: UsuariosPublic
    likes_count: int = 0
    comentarios_count: int = 0
    dio_like: bool = False  # si el usuario logueado ya dio like a este pin


# resuelve referencias entre esquemas anidados, evita NameError al arrancar
PinesPublic.model_rebuild()
ComentariosPublic.model_rebuild()


# ==============================
# ESQUEMAS DE AUTH (JWT)
# ==============================

class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuariosPublic