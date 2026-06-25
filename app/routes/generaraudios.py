# app/routes/generaraudios.py

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse
from TTS.api import TTS
import uuid
import os

router = APIRouter(prefix="/audio", tags=["Audio"])

# Modelos de voz permitidos
modelos_permitidos = {
    "es_css10": "tts_models/es/css10/vits",
    "es_mai": "tts_models/es/mai/tacotron2-DDC",
    "es_mai_vits": "tts_models/es/mai/vits",
    "en_ljspeech_tacotron2": "tts_models/en/ljspeech/tacotron2-DDC",
}

@router.post("/generar/")
async def generar_audio(
    texto: str = Body(...),
    modelo: str = Body(...)
):
    if modelo not in modelos_permitidos:
        raise HTTPException(status_code=400, detail="Modelo de voz no válido.")

    try:
        modelo_path = modelos_permitidos[modelo]
        tts = TTS(model_name=modelo_path, progress_bar=False, gpu=False)
        nombre_archivo = f"voz_{uuid.uuid4().hex}.wav"
        ruta = f"/tmp/{nombre_archivo}"
        tts.tts_to_file(text=texto, file_path=ruta)
        return FileResponse(ruta, media_type="audio/wav", filename=nombre_archivo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

