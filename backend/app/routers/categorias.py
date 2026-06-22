from fastapi import APIRouter
from sqlmodel import select

from db import SessionDep
from models import Pines


router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get("/")
def get_categorias(session: SessionDep):
    # se sacan las categorias distintas que aparecen en los pines publicos
    query = select(Pines.categoria).where(Pines.es_publico == True).distinct()
    categorias = session.exec(query).all()

    # se ordenan alfabeticamente para que la barra del front sea consistente
    return sorted(categorias)