import json
import logging
import asyncio
from typing import Optional
from app.colmena.config import settings
from app.colmena.dispatcher import connection_manager
from app.colmena.security import AgentContext

logger = logging.getLogger("colmena.tasks")

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"

TASK_TIMEOUT = 120


async def execute_agent_multimedia_task(
    task_type: str,
    prompt: str,
    user_id: int,
    role: str,
) -> dict:
    if task_type == "text":
        return await _generate_text(prompt)
    elif task_type == "video":
        return await _generate_video(prompt)
    elif task_type == "audio":
        return await _generate_audio(prompt)
    elif task_type == "image":
        return await _generate_image(prompt)
    else:
        return await _generate_text(prompt)


async def _generate_text(prompt: str) -> dict:
    try:
        from app.services.ai.mcp_service import mcp_service
        if mcp_service.available:
            result = mcp_service.generate(
                prompt=prompt,
                system_instruction="Eres un asistente educativo experto en diseño instruccional.",
                temperature=0.7,
                max_tokens=4096,
            )
            return {"status": "success", "source": "cloud", "output": result}
    except Exception as e:
        logger.warning(f"Gemini cloud failed: {e}")

    try:
        import httpx
        payload = {
            "model": "llama3.2",
            "prompt": prompt,
            "system": "Eres un asistente educativo experto en diseño instruccional.",
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        async with httpx.AsyncClient(timeout=TASK_TIMEOUT) as client:
            resp = await client.post(OLLAMA_GENERATE_URL, json=payload)
            if resp.status_code == 200:
                result = resp.json().get("response", "")
                return {"status": "success", "source": "local", "output": result}
    except Exception as e:
        logger.warning(f"Ollama fallback also failed: {e}")

    return {"status": "error", "message": "All generation backends failed"}


async def _generate_video(prompt: str) -> dict:
    import httpx
    api_key = __import__("os").getenv("DASHSCOPE_API_KEY", "")
    if api_key:
        try:
            headers = {
                "Authorization": f"Bearer {api_key.strip()}",
                "X-DashScope-Async": "enable",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "wan2.6-t2v",
                "input": {"prompt": prompt},
                "parameters": {"duration": 5},
            }
            async with httpx.AsyncClient(timeout=TASK_TIMEOUT) as client:
                resp = await client.post(
                    "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
                    json=payload,
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {"status": "success", "source": "cloud", "task_id": data.get("output", {}).get("task_id", "")}
        except Exception as e:
            logger.warning(f"Video cloud failed: {e}")

    return {"status": "error", "message": "Video generation not available (no cloud API key or fallback)"}


async def _generate_audio(prompt: str) -> dict:
    try:
        import edge_tts
        import uuid
        tts_dir = "/home/ubuntu/backend/static/tts"
        os.makedirs(tts_dir, exist_ok=True)
        filename = f"colmena_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(tts_dir, filename)
        communicate = edge_tts.Communicate(prompt, "es-CO-SalomeNeural")
        await communicate.save(filepath)
        return {"status": "success", "source": "cloud", "output": f"/static/tts/{filename}"}
    except Exception as e:
        logger.warning(f"Audio generation failed: {e}")
        return {"status": "error", "message": f"Audio generation failed: {e}"}


async def _generate_image(prompt: str) -> dict:
    try:
        from app.services.ai.mcp_service import mcp_service
        if mcp_service.available:
            result = mcp_service.generate_json(
                prompt=f"Genera una descripción detallada para una imagen educativa basada en: {prompt}",
                system_instruction="Describe imágenes educativas en detalle. Responde JSON con: {\"description\":\"...\", \"style\":\"...\"}",
                temperature=0.7,
            )
            return {"status": "success", "source": "cloud", "output": result}
    except Exception as e:
        logger.warning(f"Image cloud failed: {e}")
    return {"status": "error", "message": "Image generation not available"}


async def run_multimedia_task_and_notify(
    task_type: str,
    prompt: str,
    user_id: int,
    role: str,
):
    try:
        result = await execute_agent_multimedia_task(task_type, prompt, user_id, role)
        notification = {
            "type": "background_complete",
            "task_type": task_type,
            "source": result.get("source", "unknown"),
            "message": f"Tarea {task_type} completada" if result["status"] == "success" else f"Tarea {task_type} falló",
            "status": result["status"],
            "data": result.get("output", result.get("task_id", "")),
        }
        await connection_manager.notify_role(role, notification)
    except Exception as e:
        logger.error(f"Background task error: {e}")


import os
