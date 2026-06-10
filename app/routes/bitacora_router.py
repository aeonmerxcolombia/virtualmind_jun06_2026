# app/routes/bitacora_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List # Importar List
from datetime import date

from app.services import log_service
from app.auth.jwt_handler import verify_token
from app.models.user import User
from app.database.db import SessionLocal

router = APIRouter(prefix="/bitacora", tags=["Bitácora"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def ver_bitacora_usuario_por_documento(
    documento: str, 
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """
    Retorna la bitácora de un usuario, buscado por NÚMERO DE DOCUMENTO.
    Acepta filtrado por fechas opcional.
    """

    # 1. Buscar al usuario por su documento
    user = db.query(User).filter(User.documento == documento).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró un usuario con el documento '{documento}'"
        )
    
    # 2. Obtenemos el UID del usuario que encontramos
    usuario_id_encontrado = user.uid

    # --- CAMBIO 3: CORRECCIÓN DE PERMISOS ---
    
    # Obtenemos el UID y la LISTA de roles del token
    logged_in_user_uid = token_data.get("user_id")
    logged_in_user_roles: List[str] = token_data.get("roles", []) # <- Obtenemos la LISTA "roles" (plural)

    if not logged_in_user_uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    # Comprobamos si el usuario logueado es el dueño O si "superadmin" está EN SU LISTA de roles
    if logged_in_user_uid != usuario_id_encontrado and "superadmin" not in logged_in_user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permisos para ver esta bitácora"
        )
    # --- FIN DEL CAMBIO ---

    # 4. Llamar al servicio de log
    logs = log_service.obtener_bitacora_usuario(
        db,
        usuario_id=usuario_id_encontrado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

    return {"usuario_id": usuario_id_encontrado, "documento": documento, "bitacora": logs}
