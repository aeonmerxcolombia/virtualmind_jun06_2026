from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from google import genai

router = APIRouter(
    prefix="/lyria",
    tags=["Lyria - Música IA"]
)

class LyriaRequest(BaseModel):
    prompt: str
    model: str = "lyria-3-clip-preview"

AUDIO_DIR = "/home/ubuntu/audios/lyria"
os.makedirs(AUDIO_DIR, exist_ok=True)

@router.post("/generate")
async def generate_music(data: LyriaRequest):
    api_key = os.getenv("LYRIA_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LYRIA_API_KEY no configurada")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=data.model,
            contents=data.prompt,
        )
        lyrics = ""
        audio_data = None
        for part in response.parts:
            if part.text is not None:
                lyrics += part.text + "\n"
            elif part.inline_data is not None:
                audio_data = part.inline_data.data
        if not audio_data:
            raise HTTPException(status_code=500, detail="No se generó audio")
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(audio_data)
        audio_url = f"/audios/lyria/{filename}"
        return {
            "success": True,
            "audio_url": audio_url,
            "lyrics": lyrics.strip(),
            "model": data.model,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando música: {str(e)}")
