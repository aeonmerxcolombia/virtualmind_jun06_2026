# app/routes/documentos_router.py - Router para documentos Office

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
from pydantic import BaseModel
from datetime import datetime
import os
import uuid

from app.database.db import SessionLocal
from app.auth.jwt_handler import verify_token
from app.models.archivo import Archivo
from app.schemas.archivo_schema import ArchivoOut
from app.services.log_service import registrar_log

router = APIRouter(
    prefix="/documentos",
    tags=["Documentos"]
)

DOCUMENTOS_DIR = "/home/ubuntu/backend/static/documentos"
os.makedirs(DOCUMENTOS_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== ESQUEMAS ====================

class DocumentoCreate(BaseModel):
    nombre: str
    tipo: str  # docx, xlsx, pptx

class DocumentoOut(BaseModel):
    id: int
    nombre_archivo: str
    url: str
    tipo: Optional[str] = None
    fecha_subida: datetime
    subido_por_uid: Optional[str] = None
    folder_id: Optional[int] = None

# ==================== ENDPOINTS ====================

@router.options("/")
async def options_documentos():
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
    )

@router.get("/", response_model=List[DocumentoOut])
def list_documentos(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    """Lista solo documentos Office del usuario"""
    # Extraer user_id del token - puede ser string UUID
    uid = token_data.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Normalizar uid (puede ser string UUID o id entero)
    uid_str = str(uid) if uid else None
    
    # Obtener archivos del usuario por uid string
    archivos = db.query(Archivo).filter(
        Archivo.subido_por_uid == uid_str
    ).order_by(Archivo.fecha_subida.desc()).all()
    
    # Filtrar solo Office
    office_exts = ['docx', 'xlsx', 'pptx']
    docs = [a for a in archivos if a.nombre_archivo.split('.')[-1].lower() in office_exts]
    
    return docs

@router.post("/", response_model=DocumentoOut, status_code=status.HTTP_201_CREATED)
async def upload_documento(
    nombre_archivo: str = Form(...),
    tipo: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    """Sube un documento Office"""
    # Extraer user_id del token
    uid = token_data.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Normalizar uid a string (el modelo espera string UUID)
    uid_str = str(uid) if uid else None
    
    ext = os.path.splitext(file.filename)[1].lower().replace('.', '')
    
    # Validar tipo
    if ext not in ['docx', 'xlsx', 'pptx']:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .docx, .xlsx, .pptx")
    
    # Generar nombre único
    name = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(DOCUMENTOS_DIR, name)
    
    # Guardar archivo
    with open(path, "wb") as f:
        f.write(await file.read())
    
    url = f"https://gestordecursos.pegui.edu.co:8000/static/documentos/{name}"
    
    uid = token_data["user_id"]
    
    # Crear registro en BD
    arch = Archivo(
        nombre_archivo=nombre_archivo or file.filename,
        url=url,
        tipo=tipo or f"application/{ext}",
        subido_por_uid=uid_str,
        folder_id=None  # Sin carpeta específica
    )
    db.add(arch)
    db.commit()
    db.refresh(arch)
    
    # Log
    try:
        registrar_log(
            db=db,
            usuario_id=uid_str,
            tipo_evento="documento_office_subido",
            descripcion=f"Documento Office '{nombre_archivo}' subido"
        )
    except:
        pass
    
    return arch

@router.get("/carpetas", response_model=List[dict])
def list_carpetas(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    """Lista carpetas del usuario para documentos"""
    from app.models.folder import Folder
    uid = token_data["user_id"]
    
    carpetas = db.query(Folder).filter(
        (Folder.subido_por_uid == uid) | (Folder.subido_por_uid == None)
    ).order_by(Folder.fecha_creado.desc()).all()
    
    return [{"id": c.id, "nombre": c.nombre} for c in carpetas]

@router.post("/carpetas", status_code=status.HTTP_201_CREATED)
def create_carpeta(
    nombre: str = Form(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    """Crea una carpeta para documentos"""
    from app.models.folder import Folder
    
    uid = token_data["user_id"]
    
    folder = Folder(
        nombre=nombre,
        descripcion="Carpeta de documentos",
        subido_por_uid=uid
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    
    return folder

@router.delete("/{archivo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_documento(
    archivo_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    """Elimina un documento"""
    uid = token_data["user_id"]
    
    arch = db.query(Archivo).filter(
        Archivo.id == archivo_id,
        Archivo.subido_por_uid == uid
    ).first()
    
    if not arch:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Eliminar archivo físico
    filename = arch.url.split('/')[-1]
    filepath = os.path.join(DOCUMENTOS_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Eliminar de BD
    db.delete(arch)
    db.commit()
    
    # Log
    try:
        registrar_log(
            db=db,
            usuario_id=uid,
            tipo_evento="documento_office_eliminado",
            descripcion=f"Documento Office '{arch.nombre_archivo}' eliminado"
        )
    except:
        pass

@router.options("/")
async def options_documentos():
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
    )
