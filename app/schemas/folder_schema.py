# app/schemas/folder_schema.py

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, ForwardRef
from .archivo_schema import ArchivoOut

FolderOut = ForwardRef("FolderOut")

class FolderBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    parent_id: Optional[int]   = None

class FolderCreate(FolderBase):
    pass

class FolderUpdate(BaseModel):
    nombre: Optional[str]
    descripcion: Optional[str]
    parent_id: Optional[int]
    estado: Optional[bool]

class FolderOut(FolderBase):
    id: int
    subido_por_uid: Optional[str]
    fecha_creado: datetime
    estado: bool
    hijos: List[FolderOut]    = []
    archivos: List[ArchivoOut] = []

    class Config:
        from_attributes = True

# para que funcione la auto-referencia
FolderOut.update_forward_refs()

