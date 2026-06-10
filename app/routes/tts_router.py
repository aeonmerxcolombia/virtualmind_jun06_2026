import asyncio, os, uuid, edge_tts
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from app.auth.jwt_handler import verify_token

router = APIRouter(prefix="/ai", tags=["TTS - Edge"])
TTS_DIR = "/home/ubuntu/backend/static/tts"
os.makedirs(TTS_DIR, exist_ok=True)

class TTSRequest(BaseModel):
    text: str
    voice: str = "es-CO-SalomeNeural"
    rate: str = "0"
    pitch: str = "0"

class TTSVoice(BaseModel):
    voice: str
    gender: str
    locale: str
    display: str


def _fmt_rate(val: str) -> str:
    v = val.strip().replace('%', '')
    prefix = '+' if not v.startswith(('-', '+')) else ''
    return f"{prefix}{v}%"

def _fmt_pitch(val: str) -> str:
    v = val.strip().replace('Hz', '')
    prefix = '+' if not v.startswith(('-', '+')) else ''
    return f"{prefix}{v}Hz"

@router.post("/tts")
async def text_to_speech(req: TTSRequest, token_data: dict = Depends(verify_token)):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Texto requerido")
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(TTS_DIR, filename)
    communicate = edge_tts.Communicate(req.text, req.voice, rate=_fmt_rate(req.rate), pitch=_fmt_pitch(req.pitch))
    await communicate.save(filepath)
    return {
        "audio_url": f"https://gestordecursos.pegui.edu.co:8000/static/tts/{filename}",
        "filename": filename
    }


@router.get("/tts/voices")
async def list_voices(token_data: dict = Depends(verify_token)):
    voices = await edge_tts.list_voices()
    result = []
    for v in voices:
        result.append({
            "voice": v["ShortName"],
            "gender": v["Gender"],
            "locale": v["Locale"],
            "display": f"{v['ShortName'].replace('Neural','')} ({v['Gender']}, {v['Locale']})"
        })
    return sorted(result, key=lambda x: x["voice"])
