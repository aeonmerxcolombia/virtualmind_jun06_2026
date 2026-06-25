from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil

router = APIRouter(prefix="/config", tags=["Configuración Visual"])

UPLOAD_PATH = "/home/ubuntu/frontend/assets"  # Ruta absoluta a tu carpeta frontend real
LOGIN_BG_FILENAME = "login-bg.jpg"

os.makedirs(UPLOAD_PATH, exist_ok=True)

@router.post("/login-bg")
async def upload_login_background(image: UploadFile = File(...)):
    if not image.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Formato no válido. Usa JPG o PNG.")
    
    destino = os.path.join(UPLOAD_PATH, LOGIN_BG_FILENAME)
    with open(destino, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    return {"msg": "Imagen actualizada", "url": "/assets/login-bg.jpg"}

