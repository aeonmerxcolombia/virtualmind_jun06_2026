from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json
import asyncio
import requests
from typing import Dict, Any

# ---------------------------------------------------------
# CONFIGURACIÓN Y AUTH (Vertex comentada)
# ---------------------------------------------------------
# from google.oauth2 import service_account
# from google.auth.transport.requests import Request

router = APIRouter(tags=["IA"])

# ---------------------------------------------------------
# 🦙 OLLAMA (Respaldo Local)
# ---------------------------------------------------------
OLLAMA_API_URL = "http://localhost:11434/api/generate"


class OllamaRequest(BaseModel):
    prompt: str
    model: str = "llama3.2"


@router.post("/chat/ollama")
async def chat_ollama(request: OllamaRequest):
    """
    Endpoint de respaldo local usando Ollama.
    """
    payload = {"model": request.model, "prompt": request.prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return {"respuesta": data.get("response", "Sin respuesta de Ollama")}
    except Exception as e:
        return {"respuesta": f"❌ Error consultando Ollama Local: {str(e)}"}


# ----------------------------
# OPENAI
# ----------------------------
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


class ChatRequest(BaseModel):
    mensaje: str


@router.post("/chat/openai")
async def chat_openai(request: ChatRequest):
    try:
        response = client.responses.create(model="gpt-5.5", input=request.mensaje)
        return {"respuesta": response.output_text}
    except Exception as e:
        return {"respuesta": f"❌ Error consultando OpenAI: {str(e)}"}


# ----------------------------
# GEMINI
# ----------------------------
from app.services.ai.gemini_pool import get_gemini_key


class GeminiRequest(BaseModel):
    prompt: str


@router.post("/chat/gemini")
async def chat_gemini(request: GeminiRequest):
    prompt = request.prompt
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={get_gemini_key()}"
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(
            url, headers={"Content-Type": "application/json"}, json=body, timeout=60
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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={get_gemini_key()}"
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
    except Exception as e:
        return {"respuesta": f"❌ Error consultando Gemini: {str(e)}"}


# ---------------------------------------------------------
# 🎬 SECCIÓN DE VIDEO (COMENTADA)
# ---------------------------------------------------------
"""
PROJECT_ID = "handy-flame-418304"
LOCATION = "us-central1"
MODEL_ID = "veo-2.0-generate-001"
SERVICE_ACCOUNT_FILE = "/home/ubuntu/backend/vertex-video-service.json"

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
    url = (f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}"
           f"/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:predict")
    body = {
        "instances": [{"prompt": request.prompt}],
        "parameters": {
            "aspectRatio": request.aspect_ratio,
            "durationSeconds": request.duration,
            "generateAudio": True,
            "sampleCount": 1
        }
    }
    headers = {"Authorization": f"Bearer {get_access_token()}", "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": f"❌ Error generando video: {str(e)}"}

@router.get("/chat/video/status")
async def video_status(operation: str = Query(..., description="operation.name")):
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{operation}"
    headers = {"Authorization": f"Bearer {get_access_token()}", "Content-Type": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": f"❌ Error consultando estado: {str(e)}"}

# Google AI Studio (veo)
from google import genai
from google.genai import types
import time

GEMINI_API_KEY_STUDIO = get_gemini_key()

client_ai_studio = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=GEMINI_API_KEY_STUDIO,
)

MODEL_STUDIO = "veo-2.0-generate-001"

class VideoAIStudioRequest(BaseModel):
    prompt: str
    duration: int = 8
    aspect_ratio: str = "16:9"

@router.post("/chat/video-ai-studio")
async def generar_video_ai_studio(request: VideoAIStudioRequest):
    try:
        video_config = types.GenerateVideosConfig(
            aspect_ratio=request.aspect_ratio,
            number_of_videos=1,
            duration_seconds=request.duration,
            person_generation="ALLOW_ALL",
        )
        operation = client_ai_studio.models.generate_videos(
            model=MODEL_STUDIO,
            prompt=request.prompt,
            config=video_config,
        )
        while not operation.done:
            time.sleep(10)
            operation = client_ai_studio.operations.get(operation)
        result = operation.result
        if not result or not result.generated_videos:
            return {"error": "❌ No se generó ningún video"}
        return {"video_uri": result.generated_videos[0].video.uri}
    except Exception as e:
        return {"error": f"❌ Error generando video con AI Studio: {str(e)}"}
"""
