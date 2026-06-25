import base64
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional
import os
import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.auth.jwt_handler import verify_token
from app.services.email_service import send_email
from app.models.user import User

UPLOAD_DIR = os.path.join(os.getcwd(), "static", "uploads")
MODEL_DIR = os.path.join(os.getcwd(), "static", "models")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
PUBLIC_BASE = "https://gestordecursos.pegui.edu.co:8000"

load_dotenv()

router = APIRouter(
    prefix="/tripo3d",
    tags=["Tripo3D - Generación 3D"]
)

API_BASE = "https://api.tripo3d.ai/v2/openapi"

def get_headers():
    api_key = os.getenv("TRIPO_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="TRIPO_API_KEY no configurada")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

class TextToModelRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    model_version: Optional[str] = None
    face_limit: Optional[int] = None
    texture: Optional[bool] = None
    pbr: Optional[bool] = None
    image_seed: Optional[int] = None
    model_seed: Optional[int] = None
    texture_seed: Optional[int] = None
    texture_quality: Optional[str] = None
    geometry_quality: Optional[str] = None
    auto_size: Optional[bool] = None
    quad: Optional[bool] = None
    compress: Optional[bool] = None
    generate_parts: Optional[bool] = None
    smart_low_poly: Optional[bool] = None
    export_uv: Optional[bool] = None

class ImageToModelRequest(BaseModel):
    image: str
    model_version: Optional[str] = None
    face_limit: Optional[int] = None
    texture: Optional[bool] = None
    pbr: Optional[bool] = None
    model_seed: Optional[int] = None
    texture_seed: Optional[int] = None
    texture_quality: Optional[str] = None
    geometry_quality: Optional[str] = None
    texture_alignment: Optional[str] = None
    auto_size: Optional[bool] = None
    orientation: Optional[str] = None
    quad: Optional[bool] = None
    compress: Optional[bool] = None
    generate_parts: Optional[bool] = None
    smart_low_poly: Optional[bool] = None
    enable_image_autofix: Optional[bool] = None
    export_uv: Optional[bool] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ShareRequest(BaseModel):
    task_id: str
    recipient_email: str
    message: Optional[str] = None

def strip_none(d):
    return {k: v for k, v in d.items() if v is not None}

@router.post("/text-to-model")
async def text_to_model(data: TextToModelRequest):
    try:
        async with httpx.AsyncClient() as client:
            payload = strip_none({
                "type": "text_to_model",
                "prompt": data.prompt,
                "negative_prompt": data.negative_prompt,
                "model_version": data.model_version,
                "face_limit": data.face_limit,
                "texture": data.texture,
                "pbr": data.pbr,
                "image_seed": data.image_seed,
                "model_seed": data.model_seed,
                "texture_seed": data.texture_seed,
                "texture_quality": data.texture_quality,
                "geometry_quality": data.geometry_quality,
                "auto_size": data.auto_size,
                "quad": data.quad,
                "compress": data.compress,
                "generate_parts": data.generate_parts,
                "smart_low_poly": data.smart_low_poly,
                "export_uv": data.export_uv,
            })
            res = await client.post(f"{API_BASE}/task", headers=get_headers(), json=payload)
            data = res.json()
            if data.get("code") != 0:
                raise HTTPException(status_code=400, detail=data.get("message", "Error Tripo3D"))
            return {"task_id": data["data"]["task_id"], "status": "PENDING"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _resolve_image_url(image: str) -> dict:
    mime = "image/png"
    url = image
    if image.startswith("data:") or image.startswith("data:image/"):
        try:
            header, encoded = image.split(",", 1)
            raw = base64.b64decode(encoded)
            ext = "png"
            if "jpeg" in header or "jpg" in header:
                ext = "jpg"
                mime = "image/jpeg"
            elif "gif" in header:
                ext = "gif"
                mime = "image/gif"
            elif "webp" in header:
                ext = "webp"
                mime = "image/webp"
            filename = f"tripo3d_{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(raw)
            url = f"{PUBLIC_BASE}/static/uploads/{filename}"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error al procesar imagen base64: {e}")
    else:
        if ".jpg" in image.lower() or ".jpeg" in image.lower():
            mime = "image/jpeg"
        elif ".png" in image.lower():
            mime = "image/png"
        elif ".gif" in image.lower():
            mime = "image/gif"
        elif ".webp" in image.lower():
            mime = "image/webp"
    return {"url": url, "mime": mime}

@router.post("/image-to-model")
async def image_to_model(data: ImageToModelRequest):
    try:
        resolved = _resolve_image_url(data.image)
        async with httpx.AsyncClient() as client:
            payload = strip_none({
                "type": "image_to_model",
                "file": {
                    "type": resolved["mime"],
                    "url": resolved["url"]
                },
                "model_version": data.model_version,
                "face_limit": data.face_limit,
                "texture": data.texture,
                "pbr": data.pbr,
                "model_seed": data.model_seed,
                "texture_seed": data.texture_seed,
                "texture_quality": data.texture_quality,
                "geometry_quality": data.geometry_quality,
                "texture_alignment": data.texture_alignment,
                "auto_size": data.auto_size,
                "orientation": data.orientation,
                "quad": data.quad,
                "compress": data.compress,
                "generate_parts": data.generate_parts,
                "smart_low_poly": data.smart_low_poly,
                "enable_image_autofix": data.enable_image_autofix,
                "export_uv": data.export_uv,
            })
            res = await client.post(f"{API_BASE}/task", headers=get_headers(), json=payload)
            data = res.json()
            if data.get("code") != 0:
                raise HTTPException(status_code=400, detail=data.get("message", "Error Tripo3D"))
            return {"task_id": data["data"]["task_id"], "status": "PENDING"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{API_BASE}/task/{task_id}", headers=get_headers())
            data = res.json()
            if data.get("code") != 0:
                return {"task_id": task_id, "status": "FAILED", "error": data.get("message", "Error")}

            task_data = data["data"]
            status = task_data["status"].upper()
            result = {"task_id": task_id, "status": status}

            if status == "SUCCESS":
                output = task_data.get("output", {})
                result_data = task_data.get("result", {})

                if "pbr_model" in output:
                    model_download_url = output["pbr_model"]
                elif result_data and "pbr_model" in result_data:
                    model_download_url = result_data["pbr_model"]["url"]
                elif "model" in output:
                    model_download_url = output["model"]
                elif result_data and "model" in result_data:
                    model_download_url = result_data["model"]["url"]
                else:
                    model_download_url = None

                if model_download_url:
                    result["model_url"] = model_download_url

                result["proxy_url"] = f"/tripo3d/model/{task_id}"

                if model_download_url:
                    local_path = os.path.join(MODEL_DIR, f"{task_id}.glb")
                    if not os.path.exists(local_path):
                        try:
                            dl_res = await client.get(model_download_url)
                            if dl_res.status_code == 200:
                                os.makedirs(MODEL_DIR, exist_ok=True)
                                with open(local_path, "wb") as f:
                                    f.write(dl_res.content)
                                result["local_url"] = f"/static/models/{task_id}.glb"
                        except Exception:
                            pass
                    else:
                        result["local_url"] = f"/static/models/{task_id}.glb"

                if "rendered_image" in output:
                    result["thumbnail"] = output["rendered_image"]
                elif result_data and "rendered_image" in result_data:
                    result["thumbnail"] = result_data["rendered_image"]["url"]

                if "generated_image" in output:
                    result["generated_image"] = output["generated_image"]

            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/{task_id}")
async def proxy_model(task_id: str):
    try:
        local_path = os.path.join(MODEL_DIR, f"{task_id}.glb")
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                glb_data = f.read()
            return Response(
                content=glb_data,
                media_type="model/gltf-binary",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Content-Disposition": f'attachment; filename="model_{task_id}.glb"'
                }
            )

        async with httpx.AsyncClient() as client:
            task_res = await client.get(f"{API_BASE}/task/{task_id}", headers=get_headers())
            task_data = task_res.json()
            if task_data.get("code") != 0:
                raise HTTPException(status_code=404, detail="Task not found")

            output = task_data["data"].get("output", {})
            result_data = task_data["data"].get("result", {})

            model_url = output.get("pbr_model") or (result_data.get("pbr_model", {}).get("url") if result_data.get("pbr_model") else None)
            if not model_url:
                model_url = output.get("model") or (result_data.get("model", {}).get("url") if result_data.get("model") else None)
            if not model_url:
                raise HTTPException(status_code=404, detail="Model URL not found")

            model_res = await client.get(model_url)
            glb_data = model_res.content

            return Response(
                content=glb_data,
                media_type="model/gltf-binary",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Content-Disposition": f'attachment; filename="model_{task_id}.glb"'
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/share")
async def share_model(data: ShareRequest, token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{API_BASE}/task/{data.task_id}", headers=get_headers())
            task_data = res.json()
            if task_data.get("code") != 0:
                raise HTTPException(status_code=404, detail="Tarea no encontrada en Tripo3D")

            task_info = task_data["data"]
            status = task_info.get("status", "").upper()
            if status != "SUCCESS":
                raise HTTPException(status_code=400, detail="El modelo aún no está completo")

            output = task_info.get("output", {})
            result_data = task_info.get("result", {})
            model_url = output.get("pbr_model") or (result_data.get("pbr_model", {}).get("url") if result_data.get("pbr_model") else None)
            proxy_url = f"https://gestordecursos.pegui.edu.co/tripo3d/model/{data.task_id}"

            sender_name = token_data.get("nombre", "Un usuario")
            sender_email = token_data.get("sub", "")

            recipient = db.query(User).filter(User.email == data.recipient_email).first()
            recipient_name = recipient.nombre if recipient else data.recipient_email

            subject = f"{sender_name} te ha compartido un modelo 3D"
            msg_extra = f'\nMensaje: "{data.message}"\n' if data.message else ""
            body = f"""Hola {recipient_name},

{sender_name} ({sender_email}) te ha compartido un modelo 3D generado con IA.
{msg_extra}
Puedes verlo aquí:
{proxy_url}

¡Saludos!
Equipo VirtualMind"""

            html = f"""<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#1e293b;color:white;border-radius:12px;">
<div style="text-align:center;padding:20px 0;">
<div style="width:60px;height:60px;background:linear-gradient(135deg,#6366f1,#a855f7);border-radius:16px;display:inline-flex;align-items:center;justify-content:center;font-size:28px;margin-bottom:10px;">🧊</div>
<h2 style="margin:0;color:white;">{sender_name} te ha compartido un modelo 3D</h2>
</div>
<p style="color:#94a3b8;line-height:1.6;">Hola {recipient_name},</p>
<p style="color:#94a3b8;line-height:1.6;">{sender_name} ({sender_email}) ha usado <strong style="color:white;">Tripo3D Studio</strong> para generar un modelo 3D con IA y quiere compartirlo contigo.</p>
{f'<p style="color:#cbd5e1;background:#334155;padding:12px;border-radius:8px;font-style:italic;">"{data.message}"</p>' if data.message else ''}
<div style="text-align:center;padding:20px 0;">
<a href="{proxy_url}" style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#6366f1,#a855f7);color:white;text-decoration:none;border-radius:8px;font-weight:bold;">Ver modelo 3D</a>
</div>
<p style="color:#64748b;font-size:12px;text-align:center;">Generado con Tripo3D Studio - VirtualMind</p>
</div>"""

            sent = await send_email(data.recipient_email, subject, body, html=html)

            return {"success": sent, "recipient": data.recipient_email}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
