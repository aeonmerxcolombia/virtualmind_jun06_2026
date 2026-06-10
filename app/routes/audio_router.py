from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path

from app.database.db import get_db
from app.auth.jwt_handler import verify_token
from app.models.mensaje import Mensaje
from app.schemas.mensaje_schema import MensajeOut
from uuid import uuid4

router = APIRouter(prefix="/audio", tags=["Audio"])

AUDIO_DIR = Path("/home/ubuntu/audios")
AUDIO_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_audio(
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """Sube un archivo de audio y retorna la URL"""
    if not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser de audio")
    
    ext = audio.filename.split(".")[-1] if "." in audio.filename else "webm"
    filename = f"{uuid4()}.{ext}"
    filepath = AUDIO_DIR / filename
    
    content = await audio.read()
    filepath.write_bytes(content)
    
    return {
        "url": f"/audios/{filename}",
        "filename": filename
    }

@router.get("/{filename}")
def get_audio(filename: str):
    """Descarga el archivo de audio"""
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio no encontrado")
    return FileResponse(filepath, media_type="audio/webm")

# Función para guardar mensaje de audio
def guardar_mensaje_audio(db: Session, contenido: str, destinatario_uid: str, remitente_uid: str):
    mensaje = Mensaje(
        id=str(uuid4()),
        contenido=contenido,
        remitente_uid=remitente_uid,
        destinatario_uid=destinatario_uid
    )
    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)
    return mensaje