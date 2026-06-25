# app/routes/document_router.py
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.db import get_db
from app.models.document import Document
from app.schemas.document_schema import DocumentOut, DocumentCreate

# Configurar la carpeta de uploads
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

router = APIRouter(prefix="/documents", tags=["documents"])

# Crear un nuevo documento
@router.post("/", response_model=DocumentOut, status_code=201)
async def create_document(
    project_id: int = Form(...),
    document_type: str = Form(...),
    document_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Guardar el archivo
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Crear la URL pública del documento
    document_url = f"/{file_location}"

    # Crear el nuevo documento en la base de datos
    document = Document(
        project_id=project_id,
        document_type=document_type,
        document_name=document_name,
        document_url=document_url
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return document

# Obtener lista de documentos (CON FILTRO CORREGIDO)
@router.get("/", response_model=List[DocumentOut])
def list_documents(
    # --- 1. AÑADIR ESTE PARÁMETRO PARA RECIBIR EL ID DEL PROYECTO ---
    project_id: Optional[int] = Query(None, description="Filtrar por ID de proyecto"),
    document_type: Optional[str] = Query(None, description="Filtrar por tipo de documento"),
    db: Session = Depends(get_db)
):
    query = db.query(Document)

    # --- 2. APLICAR EL FILTRO SI SE PROPORCIONA UN project_id ---
    if project_id is not None:
        query = query.filter(Document.project_id == project_id)
        
    if document_type:
        query = query.filter(Document.document_type == document_type)
        
    documents = query.order_by(Document.id.desc()).all()
    return documents

# Obtener un documento específico por ID
@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return document
