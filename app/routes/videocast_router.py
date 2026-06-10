from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.database.db import SessionLocal
from app.auth.jwt_handler import verify_token
from app.models.videocast import Videocast
from app.services.log_service import registrar_log

router = APIRouter(prefix="/videocast", tags=["Videocast"])

VIDEOCAST_DIR = "/home/ubuntu/backend/static/videocast"
os.makedirs(VIDEOCAST_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_videocast(
    titulo: str = Form(...),
    descripcion: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp4", ".webm", ".avi", ".mov", ".mkv"]:
        raise HTTPException(status_code=400, detail="Formato no soportado")
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(VIDEOCAST_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    url = f"https://gestordecursos.pegui.edu.co:8000/static/videocast/{filename}"

    uid = token_data["user_id"]

    vc = Videocast(
        titulo=titulo,
        descripcion=descripcion,
        archivo_url=url,
        tipo=file.content_type,
        subido_por=uid,
    )
    db.add(vc)
    db.commit()
    db.refresh(vc)

    registrar_log(
        db=db,
        usuario_id=uid,
        tipo_evento="videocast_subido",
        descripcion=f"Videocast '{titulo}' subido por usuario ID {uid}"
    )
    return {
        "id": vc.id,
        "titulo": vc.titulo,
        "descripcion": vc.descripcion,
        "archivo_url": vc.archivo_url,
        "tipo": vc.tipo,
        "fecha_creacion": vc.fecha_creacion.isoformat() if vc.fecha_creacion else None,
    }

@router.get("/")
def list_videocasts(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    items = db.query(Videocast).order_by(Videocast.fecha_creacion.desc()).all()
    return [
        {
            "id": v.id,
            "titulo": v.titulo,
            "descripcion": v.descripcion,
            "archivo_url": v.archivo_url,
            "tipo": v.tipo,
            "subido_por": v.subido_por,
            "fecha_creacion": v.fecha_creacion.isoformat() if v.fecha_creacion else None,
        }
        for v in items
    ]

@router.get("/{videocast_id}")
def get_videocast(
    videocast_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    v = db.query(Videocast).filter(Videocast.id == videocast_id).first()
    if not v:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Videocast no encontrado")
    return {
        "id": v.id,
        "titulo": v.titulo,
        "descripcion": v.descripcion,
        "archivo_url": v.archivo_url,
        "tipo": v.tipo,
        "subido_por": v.subido_por,
        "fecha_creacion": v.fecha_creacion.isoformat() if v.fecha_creacion else None,
    }

@router.delete("/{videocast_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_videocast(
    videocast_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    v = db.query(Videocast).filter(Videocast.id == videocast_id).first()
    if not v:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Videocast no encontrado")
    registrar_log(
        db=db,
        usuario_id=token_data["user_id"],
        tipo_evento="videocast_eliminado",
        descripcion=f"Videocast '{v.titulo}' (ID {videocast_id}) eliminado"
    )
    db.delete(v)
    db.commit()
