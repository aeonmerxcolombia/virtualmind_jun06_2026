# app/routes/face_router.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
import numpy as np
import json
import math

from app.database.db import SessionLocal
from app.models.user import User
from app.auth.jwt_handler import create_access_token
from app.models.audit_log import AuditLog
from datetime import datetime

router = APIRouter(
    prefix="/auth/face",
    tags=["Reconocimiento Facial"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class FaceRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    embedding: list


class FaceLoginRequest(BaseModel):
    email: EmailStr
    embedding: list


def cosine_similarity(a: list, b: list) -> float:
    """Calcula similitud coseno entre dos vectores."""
    a = np.array(a)
    b = np.array(b)
    
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot / (norm_a * norm_b))


def registrar_auditoria(db: Session, user_uid: str, ip: str):
    """Registra entrada de usuario en auditoría."""
    try:
        audit = AuditLog(
            user_uid=user_uid,
            ip=ip,
            ciudad=None,
            pais=None,
            latitud=None,
            longitud=None,
            fecha_entrada=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
        return audit.id
    except Exception as e:
        print(f"Error registrando auditoría: {e}")
        return None


@router.post("/register")
def register_face(request: Request, data: FaceRegisterRequest, db: Session = Depends(get_db)):
    """Registra el embedding facial de un usuario existente."""
    
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    from app.auth.hashing import Hash
    if not Hash.verify(data.password, user.password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    
    embedding_json = json.dumps(data.embedding)
    
    try:
        db.execute(
            text("UPDATE usuarios SET face_embedding = :embedding WHERE email = :email"),
            {"embedding": embedding_json, "email": data.email}
        )
        db.commit()
    except Exception as e:
        print(f"Error guardando embedding: {e}")
        raise HTTPException(status_code=500, detail="Error al guardar embedding facial")
    
    return {"message": "Rostro registrado exitosamente", "email": data.email}


@router.post("/login")
def login_face(request: Request, data: FaceLoginRequest, db: Session = Depends(get_db)):
    """Login usando reconocimiento facial."""
    
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not user.estado:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    
    result = db.execute(
        text("SELECT face_embedding FROM usuarios WHERE email = :email"),
        {"email": data.email}
    ).fetchone()
    
    if not result or not result[0]:
        raise HTTPException(status_code=400, detail="Usuario no tiene rostro registrado. Regístralo primero.")
    
    stored_embedding = json.loads(result[0])
    
    similarity = cosine_similarity(data.embedding, stored_embedding)
    
    THRESHOLD = 0.75
    
    if similarity < THRESHOLD:
        raise HTTPException(status_code=401, detail=f"Rostro no reconocido. Similitud: {similarity:.2f}")
    
    ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    
    audit_id = registrar_auditoria(db=db, user_uid=user.uid, ip=ip)
    db.commit()
    
    access_token = create_access_token(data={
        "sub": user.email,
        "roles": [r.name for r in user.roles],
        "permissions": [p.name for r in user.roles for p in r.permissions],
        "user_id": user.uid,
        "audit_id": audit_id
    })
    
    terminos_aceptados_bool = user.terms_accepted_at is not None
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "terms_accepted": terminos_aceptados_bool,
        "similarity": round(similarity, 4)
    }


@router.get("/status/{email}")
def get_face_status(email: str, db: Session = Depends(get_db)):
    """Consulta si un usuario tiene rostro registrado."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    result = db.execute(
        text("SELECT face_embedding FROM usuarios WHERE email = :email"),
        {"email": email}
    ).fetchone()
    
    has_face = result and result[0] is not None
    
    return {
        "email": email,
        "has_face_registered": has_face
    }
