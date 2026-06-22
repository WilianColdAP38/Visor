from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlmodel import SQLModel, Session, create_engine


# se guarda en la raiz del proyecto, junto a main.py
sqlite_name = "db.sqlite3"
sqlite_url = f"sqlite:///{sqlite_name}"

# punto unico de conexion, todas las sesiones salen de aqui
engine = create_engine(sqlite_url)


# lifespan de fastapi, crea las tablas una sola vez al arrancar
@asynccontextmanager
async def create_all_tables(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


# una sesion nueva por cada request, el with garantiza que se cierre
def get_session():
    with Session(engine) as session:
        yield session


# atajo para inyectar la sesion en los endpoints sin repetir Depends
SessionDep = Annotated[Session, Depends(get_session)]