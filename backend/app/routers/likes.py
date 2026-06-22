from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import func, select

from db import SessionDep
from models import Usuarios, Pines, Likes
from app.auth import get_current_user


router = APIRouter(prefix="/pines", tags=["Likes"])


@router.post("/{pin_id}/like", status_code=status.HTTP_201_CREATED)
def dar_like(
    pin_id: int,
    session: SessionDep,
    usuario_actual: Usuarios = Depends(get_current_user),
):
    # el pin debe existir, estar activo y ser publico para poder recibir likes
    pin = session.get(Pines, pin_id)
    if not pin or pin.deleted_at is not None or not pin.es_publico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El pin no fue encontrado",
        )

    # si el usuario ya dio like, no se duplica el registro, idempotente
    existente = session.exec(
        select(Likes).where(
            (Likes.pin_id == pin_id) & (Likes.usuario_id == usuario_actual.id)
        )
    ).first()

    if existente:
        # se devuelve el conteo actual sin crear otro registro
        total = session.exec(
            select(func.count(Likes.id)).where(Likes.pin_id == pin_id)
        ).one()
        return {"pin_id": pin_id, "dio_like": True, "likes_count": total}

    # crea el like, usuario_id sale del token, NUNCA del body
    nuevo_like = Likes(
        usuario_id=usuario_actual.id,
        pin_id=pin_id,
    )

    session.add(nuevo_like)
    session.commit()

    # cuenta likes despues del insert para devolver el total actualizado al front
    total = session.exec(
        select(func.count(Likes.id)).where(Likes.pin_id == pin_id)
    ).one()

    return {"pin_id": pin_id, "dio_like": True, "likes_count": total}


@router.delete("/{pin_id}/like")
def quitar_like(
    pin_id: int,
    session: SessionDep,
    usuario_actual: Usuarios = Depends(get_current_user),
):
    # busca el like del usuario actual en este pin
    like_db = session.exec(
        select(Likes).where(
            (Likes.pin_id == pin_id) & (Likes.usuario_id == usuario_actual.id)
        )
    ).first()

    # si nunca dio like se trata como exito silencioso, idempotente
    if not like_db:
        total = session.exec(
            select(func.count(Likes.id)).where(Likes.pin_id == pin_id)
        ).one()
        return {"pin_id": pin_id, "dio_like": False, "likes_count": total}

    session.delete(like_db)
    session.commit()

    total = session.exec(
        select(func.count(Likes.id)).where(Likes.pin_id == pin_id)
    ).one()

    return {"pin_id": pin_id, "dio_like": False, "likes_count": total}