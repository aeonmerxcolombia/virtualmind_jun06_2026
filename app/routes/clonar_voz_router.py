import os, uuid, tempfile, io, json, time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from app.auth.jwt_handler import verify_token

router = APIRouter(prefix="/ai", tags=["Voice Cloning - XTTS"])

CLONE_DIR = "/home/ubuntu/backend/static/clonaciones"
os.makedirs(CLONE_DIR, exist_ok=True)

_tts_model = None

def _get_model():
    global _tts_model
    if _tts_model is None:
        from TTS.api import TTS
        _tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)
    return _tts_model

@router.post("/clone-voice")
async def clone_voice(
    audio: UploadFile = File(...),
    text: str = Form(...),
    language: str = Form("es"),
    token_data: dict = Depends(verify_token),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Texto requerido")
    if not audio.filename:
        raise HTTPException(status_code=400, detail="Archivo de audio requerido")

    try:
        model = _get_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando modelo XTTS: {str(e)}")

    audio_bytes = await audio.read()
    if len(audio_bytes) < 1024:
        raise HTTPException(status_code=400, detail="El audio es demasiado corto (mínimo 1KB)")

    suf = audio.filename.rsplit(".", 1)[-1] if "." in audio.filename else "wav"
    with tempfile.NamedTemporaryFile(suffix=f".{suf}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    out_name = f"clon_{uuid.uuid4().hex}.wav"
    out_path = os.path.join(CLONE_DIR, out_name)

    try:
        start = time.time()
        model.tts_to_file(
            text=text,
            file_path=out_path,
            speaker_wav=tmp_path,
            language=language,
        )
        elapsed = time.time() - start
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Error generando clonación: {str(e)}")

    os.unlink(tmp_path)

    return {
        "audio_url": f"https://gestordecursos.pegui.edu.co:8000/static/clonaciones/{out_name}",
        "filename": out_name,
        "duration_ms": int(elapsed * 1000),
    }
