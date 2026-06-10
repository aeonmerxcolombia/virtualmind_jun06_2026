from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.db import get_db
from app.auth.jwt_handler import verify_token
from app.models.user import User

router = APIRouter(prefix="/presence", tags=["Presencia"])

@router.post("/heartbeat")
def heartbeat(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """Actualiza el estado online del usuario."""
    user_id = token_data["user_id"]
    user = db.query(User).filter(User.uid == user_id).first()
    
    if user:
        user.is_online = True
        user.last_seen = datetime.now()
        db.commit()
    
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@router.get("/status")
def get_status(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """Obtiene el estado de todos los usuarios."""
    users = db.query(User.uid, User.nombre, User.email, User.is_online, User.last_seen).all()
    
    now = datetime.now()
    result = []
    
    for u in users:
        # Calcular hace cuánto estuvo activo
        last_seen_str = None
        if u.last_seen:
            diff = (now - u.last_seen).total_seconds()
            if diff < 60:
                last_seen_str = "Activo ahora"
            elif diff < 3600:
                minutes = int(diff / 60)
                last_seen_str = f"Hace {minutes} min"
            elif diff < 86400:
                hours = int(diff / 3600)
                last_seen_str = f"Hace {hours}h"
            else:
                last_seen_str = f"Hace {int(diff / 86400)} días"
        
        result.append({
            "uid": u.uid,
            "nombre": u.nombre,
            "email": u.email,
            "is_online": u.is_online,
            "last_seen": last_seen_str
        })
    
    return result