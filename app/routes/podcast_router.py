# app/routes/podcast_router.py

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form
)
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import asyncio
import edge_tts

from app.database.db import SessionLocal
from app.auth.jwt_handler import verify_token
from app.models.podcast import Podcast
from app.schemas.podcast_schema import PodcastOut, PodcastCreate
from app.services.log_service import registrar_log
from app.routes.tts_router import _fmt_rate, _fmt_pitch

router = APIRouter(
    prefix="/podcasts",
    tags=["Podcasts"]
)

PODCAST_DIR = "/home/ubuntu/backend/static/podcasts"
os.makedirs(PODCAST_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    

# Subir podcast con archivo (mp3, wav) y metadata
@router.post(
    "/",
    response_model=PodcastOut,
    status_code=status.HTTP_201_CREATED
)
async def upload_podcast(
    titulo: str = Form(...),
    descripcion: Optional[str] = Form(None),
    duracion_segundos: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    UPLOAD_DIR = "/home/ubuntu/backend/static/podcasts"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".webm", ".ogg"]:
        raise HTTPException(status_code=400, detail="Formato no soportado")
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    url = f"https://gestordecursos.pegui.edu.co:8000/static/podcasts/{filename}"

    uid = token_data["user_id"]

    podcast = Podcast(
        titulo=titulo,
        descripcion=descripcion,
        archivo_url=url,
        tipo=file.content_type,
        subido_por=uid,
        duracion_segundos=duracion_segundos
    )
    db.add(podcast)
    db.commit()
    db.refresh(podcast)

    registrar_log(
        db=db,
        usuario_id=uid,
        tipo_evento="podcast_subido",
        descripcion=f"Podcast '{titulo}' subido por usuario ID {uid}"
    )
    return podcast

@router.post("/generar", response_model=PodcastOut, status_code=status.HTTP_201_CREATED)
async def generate_podcast(
    titulo: str = Form(...),
    descripcion: Optional[str] = Form(None),
    texto: str = Form(...),
    voz: str = Form("es-CO-SalomeNeural"),
    rate: str = Form("0"),
    pitch: str = Form("0"),
    usar_clonacion: bool = Form(False),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    uid = token_data["user_id"]

    if usar_clonacion:
        filename = f"podcast_clon_{uuid.uuid4().hex}.wav"
        filepath = os.path.join(PODCAST_DIR, filename)
        try:
            from app.routes.clonar_voz_router import _get_model
            model = _get_model()
            model.tts_to_file(text=texto, file_path=filepath, language="es")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en clonación de voz: {str(e)}")
    else:
        filename = f"podcast_tts_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(PODCAST_DIR, filename)
        try:
            communicate = edge_tts.Communicate(texto, voz, rate=_fmt_rate(rate), pitch=_fmt_pitch(pitch))
            await communicate.save(filepath)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en TTS: {str(e)}")

    url = f"https://gestordecursos.pegui.edu.co:8000/static/podcasts/{filename}"

    podcast = Podcast(
        titulo=titulo,
        descripcion=descripcion,
        archivo_url=url,
        tipo="audio/mpeg" if not usar_clonacion else "audio/wav",
        subido_por=uid,
        duracion_segundos=None,
    )
    db.add(podcast)
    db.commit()
    db.refresh(podcast)

    registrar_log(
        db=db,
        usuario_id=uid,
        tipo_evento="podcast_generado_ia",
        descripcion=f"Podcast '{titulo}' generado con IA por usuario ID {uid}"
    )
    return podcast

# Listar todos los podcasts (sin filtros)
@router.get(
    "/",
    response_model=List[PodcastOut]
)
def list_podcasts(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    return db.query(Podcast).order_by(Podcast.fecha_creacion.desc()).all()

# Obtener podcast individual
@router.get(
    "/{podcast_id}",
    response_model=PodcastOut
)
def get_podcast(
    podcast_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Podcast no encontrado")
    return podcast

# Eliminar podcast
@router.delete(
    "/{podcast_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_podcast(
    podcast_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Podcast no encontrado")
    registrar_log(
        db=db,
        usuario_id=token_data["user_id"],
        tipo_evento="podcast_eliminado",
        descripcion=f"Podcast '{podcast.titulo}' (ID {podcast_id}) eliminado por usuario ID {token_data['user_id']}"
    )
    db.delete(podcast)
    db.commit()

