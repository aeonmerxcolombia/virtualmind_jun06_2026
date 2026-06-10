from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.client_document import ClientDocument
from app.schemas.client_document_schema import ClientDocumentOut
import os
import uuid

router = APIRouter(prefix="/client-documents", tags=["Client Documents"])

UPLOAD_DIR = "/home/ubuntu/backend/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=ClientDocumentOut)
async def upload_document(
    user_id: str = Form(...),
    tipo_documento: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    ext = os.path.splitext(file.filename)[1]
    name = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f:
        f.write(await file.read())
    url = f"https://144.217.76.64:8000/static/uploads/{name}"

    doc = ClientDocument(
        id=str(uuid.uuid4()),
        user_id=user_id,
        tipo_documento=tipo_documento,
        archivo_url=url
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

@router.get("/{user_id}", response_model=list[ClientDocumentOut])
def list_documents(user_id: str, db: Session = Depends(get_db)):
    return db.query(ClientDocument).filter(ClientDocument.user_id == user_id).all()

