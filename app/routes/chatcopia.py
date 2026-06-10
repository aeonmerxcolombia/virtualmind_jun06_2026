from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json
import asyncio
import requests
from typing import Dict, Any

# Google Auth para Vertex
from google.oauth2 import service_account
from google.auth.transport.requests import Request

router = APIRouter(tags=["IA"])

# ----------------------------
# OPENAI
# ----------------------------
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


class ChatRequest(BaseModel):
    mensaje: str


@router.post("/chat/openai", response_class=StreamingResponse)
async def chat_openai(request: ChatRequest):
    mensaje = request.mensaje
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "stream": True,
        "messages": [
            {"role": "system", "content": "Eres un asistente útil de Virtualmind."},
            {"role": "user", "content": mensaje},
        ],
    }

    async def stream_openai():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        content = line[6:]
                        if content.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(content)
                            delta = data["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                                await asyncio.sleep(0.01)
                        except Exception:
                            continue

    return StreamingResponse(stream_openai(), media_type="text/plain")


# ----------------------------
# GEMINI
# ----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


class GeminiRequest(BaseModel):
    prompt: str


@router.post("/chat/gemini")
async def chat_gemini(request: GeminiRequest):
    prompt = request.prompt
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(
            url, headers={"Content-Type": "application/json"}, json=body, timeout=30
        )
        data = response.json()
        respuestaIA = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "Sin respuesta")
        )
        return {"respuesta": respuestaIA}
    except Exception as e:
        return {"respuesta": f"❌ Error consultando Gemini: {str(e)}"}


# ----------------------------
# KIMI
# ----------------------------
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")


class KimiRequest(BaseModel):
    mensaje: str


@router.post("/chat/kimi")
async def chat_kimi(request: KimiRequest):
    mensaje = request.mensaje
    headers = {
        "Authorization": f"Bearer {KIMI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "kimi",
        "messages": [{"role": "user", "content": mensaje}],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://kimi-k2.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {"respuesta": content}
    except Exception as e:
        return {"respuesta": f"❌ Error consultando Kimi: {str(e)}"}


# ----------------------------
# GEMINI GENERAR CONTENIDO
# ----------------------------
class GenerarContenidoRequest(BaseModel):
    prompt: str


@router.post("/chat/generar-contenido")
async def generar_contenido(request: GenerarContenidoRequest):
    GEMINI_API_KEY_FORM = os.getenv("GEMINI_API_KEY", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY_FORM}"
    body = {"contents": [{"parts": [{"text": request.prompt}]}]}
    try:
        response = requests.post(
            url, headers={"Content-Type": "application/json"}, json=body, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        respuestaIA = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "Sin respuesta de la IA.")
        )
        return {"respuesta": respuestaIA}
    except requests.exceptions.HTTPError as http_err:
        return {
            "respuesta": f"❌ Error HTTP: {http_err}. Verifica API Key y modelo Gemini."
        }
    except Exception as e:
        return {"respuesta": f"❌ Error consultando Gemini: {str(e)}"}


# ----------------------------
# GOOGLE VEO (VIDEO)
# ----------------------------
PROJECT_ID = "handy-flame-418304"
LOCATION = "us-central1"
MODEL_ID = "veo-2.0-generate-001"
SERVICE_ACCOUNT_FILE = "/home/ubuntu/backend/vertex-video-service.json"


# 🔑 Generar token
def get_access_token():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token


class VideoRequest(BaseModel):
    prompt: str
    duration: int = 8
    aspect_ratio: str = "16:9"


@router.post("/chat/video")
async def generar_video(request: VideoRequest):
    """
    Inicia la generación de video con Google Veo (Vertex AI).
    Devuelve un operation.name válido para polling.
    """
    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}"
        f"/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:predict"
    )

    body = {
        "instances": [{"prompt": request.prompt}],
        "parameters": {
            "aspectRatio": request.aspect_ratio,
            "durationSeconds": request.duration,
            "generateAudio": True,
            "sampleCount": 1,
        },
    }

    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"❌ Error HTTP: {http_err}", "detalle": resp.text}
    except Exception as e:
        return {"error": f"❌ Error generando video: {str(e)}"}


@router.get("/chat/video/status")
async def video_status(
    operation: str = Query(
        ..., description="operation.name devuelto al iniciar el video"
    ),
):
    """
    Consulta el estado de la operación de generación de video en Vertex AI.
    """
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{operation}"
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as http_err:
        return {
            "error": f"❌ Error HTTP: {http_err}",
            "detalle": resp.text,
            "url_consultada": url,
        }
    except Exception as e:
        return {"error": f"❌ Error consultando estado: {str(e)}"}


# ================================
# 🎬 Nuevo endpoint con Google AI Studio (veo)
# ================================

from google import genai
from google.genai import types
import time

# API Key de AI Studio (segura)
GEMINI_API_KEY_STUDIO = "YOUR_GEMINI_STUDIO_KEY"

client_ai_studio = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=GEMINI_API_KEY_STUDIO,
)

MODEL_STUDIO = "veo-2.0-generate-001"  # también puedes probar "veo-3.0-generate-001"


class VideoAIStudioRequest(BaseModel):
    prompt: str
    duration: int = 8
    aspect_ratio: str = "16:9"


@router.post("/chat/video-ai-studio")
async def generar_video_ai_studio(request: VideoAIStudioRequest):
    """
    Genera video usando Google AI Studio (veo).
    Este endpoint usa el SDK oficial `google-genai`.
    """
    try:
        video_config = types.GenerateVideosConfig(
            aspect_ratio=request.aspect_ratio,
            number_of_videos=1,
            duration_seconds=request.duration,
            person_generation="ALLOW_ALL",
        )

        # Inicia la operación
        operation = client_ai_studio.models.generate_videos(
            model=MODEL_STUDIO,
            prompt=request.prompt,
            config=video_config,
        )

        # Polling hasta que termine
        while not operation.done:
            time.sleep(10)
            operation = client_ai_studio.operations.get(operation)

        result = operation.result
        if not result or not result.generated_videos:
            return {"error": "❌ No se generó ningún video"}

        video_uri = result.generated_videos[0].video.uri
        return {"video_uri": video_uri}

    except Exception as e:
        return {"error": f"❌ Error generando video con AI Studio: {str(e)}"}
