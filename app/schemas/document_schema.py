# app/schemas/document_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime  # Para fechas

# Base común para todos los documentos
class DocumentBase(BaseModel):
    document_type: str = Field(..., example="Contrato")
    document_name: str = Field(..., example="Contrato 2025")
    document_url: str = Field(..., example="/static/uploads/contrato_2025.pdf")

# Esquema para crear un documento
class DocumentCreate(DocumentBase):
    pass

# Esquema para actualizar un documento
class DocumentUpdate(BaseModel):
    document_type: Optional[str]
    document_name: Optional[str]
    document_url: Optional[str]

# Esquema de salida para los documentos, que incluye el ID y las fechas
class DocumentOut(DocumentBase):
    id: int
    created_at: Optional[datetime]
   

    class Config:
        from_attributes = True

