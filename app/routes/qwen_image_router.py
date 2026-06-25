# app/routes/qwen_image_router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import requests
import base64
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

router = APIRouter(
    prefix="/ai",
    tags=["IA Generativa - Qwen Image"]
)

# --- CONFIGURACIÓN DE REGIÓN: INTERNACIONAL ---
# Usamos la API síncrona recomendada para los modelos top como qwen-image-2.0-pro
BASE_URL = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

# --- ESTRUCTURA DE DATOS ---
class ImagePrompt(BaseModel):
    prompt: str
    negative_prompt: str = "Low resolution, blurry, distorted, malformed, bad quality"
    model: str = "qwen-image-2.0-pro" # El modelo recomendado en la doc
    size: str = "2048*2048"
    prompt_extend: bool = True

# --- ENDPOINT: GENERAR IMAGEN SÍNCRONA ---
@router.post("/generate-image")
def generate_image(data: ImagePrompt):
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Error crítico: DASHSCOPE_API_KEY no configurada en el servidor.")

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    # Payload adaptado estrictamente a la documentación de Qwen-Image 2.0 Pro
    payload = {
        "model": data.model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": data.prompt}
                    ]
                }
            ]
        },
        "parameters": {
            "negative_prompt": data.negative_prompt,
            "prompt_extend": data.prompt_extend,
            "watermark": False,
            "size": data.size
        }
    }

    print(f"🎨 Solicitando render de imagen a Alibaba (Modelo: {data.model})...")

    try:
        # Petición a DashScope
        response = requests.post(BASE_URL, headers=headers, json=payload)

        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get("message", "Error desconocido del proveedor")
            print(f"❌ Error DashScope: {error_msg}")
            raise HTTPException(status_code=400, detail=f"Error de proveedor: {error_msg}")

        result = response.json()
        
        # Extraer la URL de la imagen generada según la estructura JSON de la doc
        try:
            image_url = result["output"]["choices"][0]["message"]["content"][0]["image"]
        except (KeyError, IndexError):
            raise HTTPException(status_code=500, detail="La API de Alibaba no retornó una estructura de imagen válida.")

        # --- ADAPTACIÓN PARA TU FRONTEND ---
        # DashScope devuelve una URL temporal (24h). Como tu frontend de CKEditor
        # espera un Base64 (en "data.images[0]"), lo descargamos y convertimos aquí.
        print("📥 Descargando imagen para convertirla a Base64...")
        img_response = requests.get(image_url)
        
        if img_response.status_code == 200:
            img_base64 = base64.b64encode(img_response.content).decode("utf-8")
            return {
                "message": "Imagen generada y procesada correctamente",
                "image_url": image_url, # URL original de Alibaba (por si la necesitas guardar)
                "images": [img_base64]  # Arreglo Base64, ¡Compatible 100% con tu frontend actual!
            }
        else:
            raise HTTPException(status_code=500, detail="Se generó la imagen, pero el servidor falló al descargarla de Alibaba.")

    except requests.exceptions.RequestException as e:
        print(f"Falla de red: {e}")
        raise HTTPException(status_code=502, detail="Error de comunicación con la nube de IA.")
