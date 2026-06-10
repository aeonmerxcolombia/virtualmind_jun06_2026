# app/routes/archivo_router.py

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form
)
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid

from app.database.db import SessionLocal
from app.auth.jwt_handler import verify_token
from app.models.archivo import Archivo
from app.schemas.archivo_schema import ArchivoOut
from app.services.log_service import registrar_log

router = APIRouter(
    prefix="/archivos",
    tags=["Archivos"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🟢 SUBIR ARCHIVO PERSONAL (con carpeta opcional)
@router.post(
    "/",
    response_model=ArchivoOut,
    status_code=status.HTTP_201_CREATED
)
async def upload_archivo(
    nombre_archivo: str     = Form(...),
    tipo: Optional[str]     = Form(None),
    file: UploadFile        = File(...),
    folder_id: Optional[int] = Form(None),
    db: Session             = Depends(get_db),
    token_data: dict        = Depends(verify_token),
):
    UPLOAD_DIR = "/home/ubuntu/backend/static/uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    name = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f:
        f.write(await file.read())
    url = f"https://gestordecursos.pegui.edu.co:8000/static/uploads/{name}"

    uid = token_data["user_id"]
    arch = Archivo(
        nombre_archivo = nombre_archivo,
        url            = url,
        tipo           = tipo or file.content_type,
        subido_por_uid = uid,
        folder_id      = folder_id
    )
    db.add(arch)
    db.commit()
    db.refresh(arch)
    registrar_log(
    db=db,
    usuario_id=uid,
    tipo_evento="archivo_subido",
    descripcion=f"Archivo '{nombre_archivo}' subido por el usuario ID {uid} a carpeta {folder_id}"
    )
    return arch

# 🟢 SUBIR ARCHIVO GLOBAL (carpeta_id fijo = 4)
@router.post(
    "/global",
    response_model=ArchivoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Sube un archivo al Repositorio Público"
)
async def upload_archivo_global(
    nombre_archivo: str     = Form(...),
    tipo: Optional[str]     = Form(None),
    file: UploadFile        = File(...),
    db: Session             = Depends(get_db),
    token_data: dict        = Depends(verify_token),
):
    UPLOAD_DIR = "/home/ubuntu/backend/static/uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    name = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f:
        f.write(await file.read())
    url = f"https://gestordecursos.pegui.edu.co:8000/static/uploads/{name}"

    uid = token_data["user_id"]
    arch = Archivo(
        nombre_archivo = nombre_archivo,
        url            = url,
        tipo           = tipo or file.content_type,
        subido_por_uid = uid,
        folder_id      = 4
    )
    db.add(arch)
    db.commit()
    db.refresh(arch)
    registrar_log(
    db=db,
    usuario_id=uid,
    tipo_evento="archivo_subido_global",
    descripcion=f"Archivo global '{nombre_archivo}' subido por el usuario ID {uid}"
    )
    return arch

# ✅ LISTAR ARCHIVOS GLOBALES (antes del archivo_id para evitar conflictos)
@router.get(
    "/globales",
    response_model=List[ArchivoOut],
    summary="Listar archivos globales",
    description="Devuelve archivos que están en la carpeta global (folder_id = 4)"
)
def list_archivos_globales(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    return db.query(Archivo).filter(Archivo.folder_id == 4).order_by(Archivo.fecha_subida.desc()).all()

# ✅ LISTAR ARCHIVOS PROPIOS o GLOBAL NULL
@router.get(
    "/",
    response_model=List[ArchivoOut]
)
def list_archivos(
    mine: bool = False,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    q = db.query(Archivo)
    if mine:
        q = q.filter(Archivo.subido_por_uid == token_data["user_id"])
    else:
        q = q.filter(Archivo.subido_por_uid == None)
    return q.order_by(Archivo.fecha_subida.desc()).all()

# ✅ CONSULTAR ARCHIVO INDIVIDUAL
@router.get(
    "/{archivo_id}",
    response_model=ArchivoOut
)
def get_archivo(
    archivo_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    arch = db.query(Archivo).filter(Archivo.id == archivo_id).first()
    if not arch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    return arch

# ✅ ELIMINAR ARCHIVO
@router.delete(
    "/{archivo_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_archivo(
    archivo_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    arch = db.query(Archivo).filter(Archivo.id == archivo_id).first()
    if not arch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    registrar_log(
    db=db,
    usuario_id=token_data["user_id"],
    tipo_evento="archivo_eliminado",
    descripcion=f"Archivo '{arch.nombre_archivo}' (ID {archivo_id}) eliminado por el usuario ID {token_data['user_id']}"
    )
    db.delete(arch)
    db.commit()

# Callback para OnlyOffice - guardar cambios
@router.post("/callback/{archivo_id}")
async def callback_onlyoffice(
    archivo_id: int,
    db: Session = Depends(get_db),
):
    """Callback de OnlyOffice para guardar cambios"""
    import asyncio
    
    # This endpoint receives POST requests from OnlyOffice after save
    # For now, just acknowledge the callback
    return {"error": 0, "message": "OK"}

