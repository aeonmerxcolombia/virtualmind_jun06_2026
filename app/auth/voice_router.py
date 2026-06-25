import os
import math
import tempfile
import numpy as np
import torch
import torchaudio
import librosa

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from app.database.db import SessionLocal
from app.models.user import User
from app.auth.jwt_handler import create_access_token

router = APIRouter(
    prefix="/auth/voice",
    tags=["Autenticación por Voz"]
)

_SpeakerModel = None

def get_speaker_model():
    global _SpeakerModel
    if _SpeakerModel is None:
        from speechbrain.inference.speaker import SpeakerRecognition
        _SpeakerModel = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="/home/ubuntu/backend/pretrained_models/spkrec-ecapa-voxceleb"
        )
    return _SpeakerModel

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def extract_embedding_from_bytes(audio_bytes: bytes) -> List[float]:
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        signal, fs = librosa.load(tmp_path, sr=16000, mono=True)
        if len(signal) < 8000:
            raise HTTPException(status_code=400, detail="El audio es demasiado corto (mínimo 0.5s)")

        signal_tensor = torch.from_numpy(signal).float().unsqueeze(0)
        model = get_speaker_model()
        embedding = model.encode_batch(signal_tensor)
        return embedding.squeeze().tolist()
    finally:
        os.unlink(tmp_path)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    aa = np.array(a, dtype=np.float64)
    bb = np.array(b, dtype=np.float64)
    return float(np.dot(aa, bb) / (np.linalg.norm(aa) * np.linalg.norm(bb) + 1e-10))


@router.post("/register")
async def register_voice(
    email: str = Form(...),
    password: str = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    from app.auth.hashing import Hash
    if not Hash.verify(password, user.password):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    audio_bytes = await audio.read()
    if len(audio_bytes) < 4096:
        raise HTTPException(status_code=400, detail="El archivo de audio es demasiado pequeño")

    try:
        embedding = extract_embedding_from_bytes(audio_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")

    try:
        user.voice_embedding = embedding
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar huella de voz: {str(e)}")

    return {"message": "Huella de voz registrada exitosamente", "status": "ok"}


@router.post("/login")
async def login_voice(
    email: str = Form(...),
    audio: UploadFile = File(...),
    req: Request = None,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no registrado")
    if not user.estado:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    if not user.voice_embedding:
        raise HTTPException(status_code=400, detail="No tienes una huella de voz registrada. Regístrala primero.")

    audio_bytes = await audio.read()
    if len(audio_bytes) < 4096:
        raise HTTPException(status_code=400, detail="El archivo de audio es demasiado pequeño")

    try:
        new_embedding = extract_embedding_from_bytes(audio_bytes)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")

    similarity = cosine_similarity(user.voice_embedding, new_embedding)
    threshold = 0.55

    if similarity < threshold:
        raise HTTPException(status_code=401, detail=f"Voz no reconocida (similitud: {similarity:.3f}). Acceso denegado.")

    ip = req.client.host if req and req.client else "unknown"
    if req:
        forwarded = req.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()

    access_token = create_access_token(data={
        "sub": user.email,
        "nombre": user.nombre,
        "roles": [r.name for r in user.roles],
        "permissions": [p.name for r in user.roles for p in r.permissions],
        "user_id": user.uid
    })

    terminos_aceptados_bool = user.terms_accepted_at is not None

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "terms_accepted": terminos_aceptados_bool,
        "similarity": round(similarity, 3)
    }


class VoiceStatusRequest(BaseModel):
    email: EmailStr

@router.post("/status")
def voice_status(request: VoiceStatusRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"registered": user.voice_embedding is not None}
