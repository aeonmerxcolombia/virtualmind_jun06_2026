# app/routes/wanx_router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

router = APIRouter(
    prefix="/ai",
    tags=["IA Generativa - Wanx Video"]
)

# --- CONFIGURACIÓN DE REGIÓN: INTERNACIONAL ---
BASE_URL = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
TASK_URL = "https://dashscope-intl.aliyuncs.com/api/v1/tasks"

# --- ESTRUCTURA DE DATOS ---
class VideoPrompt(BaseModel):
    prompt: str
    model: str = "wan2.6-t2v" # Versión de producción actual
    duration: int = 5

# --- ENDPOINT 1: INICIAR GENERACIÓN ---
@router.post("/generate-video")
def start_video_generation(data: VideoPrompt):
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Error crítico: DASHSCOPE_API_KEY no configurada en el servidor.")

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "X-DashScope-Async": "enable",
        "Content-Type": "application/json"
    }

    # Payload adaptado para Wan 2.6 en DashScope
    payload = {
        "model": data.model,
        "input": {
            "prompt": data.prompt
        },
        "parameters": {
            "size": "1280*720",
            "duration": data.duration,
            "prompt_extend": True
        }
    }

    print(f"📡 Solicitando render a Alibaba (Modelo: {data.model})...")

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get("message", "Error desconocido del proveedor")
            print(f"❌ Error DashScope: {error_msg}")
            raise HTTPException(status_code=400, detail=f"Error de proveedor: {error_msg}")

        result = response.json()
        task_id = result.get("output", {}).get("task_id")

        if not task_id:
            raise HTTPException(status_code=500, detail="La API no retornó un task_id válido.")

        return {
            "message": "Pipeline de video iniciado correctamente",
            "task_id": task_id,
            "status": "PENDING"
        }

    except requests.exceptions.RequestException as e:
        print(f"Falla de red: {e}")
        raise HTTPException(status_code=502, detail="Error de comunicación con la nube de IA.")

# --- ENDPOINT 2: CONSULTAR ESTADO ---
@router.get("/status/{task_id}")
def check_video_status(task_id: str):
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Error crítico: DASHSCOPE_API_KEY no configurada.")

    headers = {"Authorization": f"Bearer {api_key.strip()}"}

    try:
        url = f"{TASK_URL}/{task_id}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Fallo al consultar a DashScope: {response.text}")

        data = response.json()
        output = data.get("output", {})
        status = output.get("task_status", "UNKNOWN")

        res_data = {
            "task_id": task_id,
            "status": status,
            "progress": 0,
        }

        if status == "SUCCEEDED":
            res_data["video_url"] = output.get("video_url")

        if status in ["FAILED", "CANCELED"]:
            res_data["error"] = data.get("message", "Falla interna en la generación de IA.")
            res_data["error_code"] = data.get("code", "")

        return res_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail="Error de red consultando el status del job.")
