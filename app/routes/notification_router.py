# app/routes/notification_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services import log_service
from app.auth.jwt_handler import verify_token
from app.models.log_model import LogAccion

router = APIRouter(prefix="/notifications", tags=["Notificaciones"])

@router.get("/")
def mis_notificaciones(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """
    Retorna las notificaciones (logs) del usuario autenticado.
    """
    user_id = token_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido o usuario no encontrado")

    # Usamos la función que filtra solo las notificaciones del usuario
    logs = log_service.obtener_notificaciones_usuario(db, usuario_id=user_id)

    if not logs:
        return {"notificaciones": [], "msg": "No tienes notificaciones"}

    # Agregar campo link a las notificaciones
    notificaciones_con_link = []
    for n in logs:
        notificaciones_con_link.append({
            "id": n["id"],
            "usuario_id": n["usuario_id"],
            "usuario": n["usuario"],
            "tipo_evento": n["tipo_evento"],
            "descripcion": n["descripcion"],
            "fecha": n["fecha"],
            "link": n.get("link")  # Campo link para hacer clickeable
        })
    
    return {"notificaciones": notificaciones_con_link}


@router.post("/leer")
def marcar_como_leido(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """
    Marca todas las notificaciones como leídas.
    """
    user_id = token_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    db.query(LogAccion).filter(
        LogAccion.usuario_id == user_id,
        LogAccion.leido == False
    ).update({"leido": True})
    db.commit()

    return {"msg": "Notificaciones marcadas como leídas"}


@router.get("/contador")
def get_contador_no_leidas(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """
    Retorna el número de notificaciones no leídas.
    """
    user_id = token_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    count = db.query(LogAccion).filter(
        LogAccion.usuario_id == user_id,
        LogAccion.leido == False
    ).count()

    return {"sin_leer": count}

