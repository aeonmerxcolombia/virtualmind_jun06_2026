from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentoBibliotecaOut(BaseModel):
    id: int
    documento_id: int
    project_id: Optional[int] = None
    nombre: str
    tipo: str
    version: str
    filename: str
    usuario_id: str
    usuario_nombre: Optional[str] = None
    proyecto_nombre: Optional[str] = None
    descripcion: Optional[str] = None
    etiquetas: Optional[str] = None
    nota_bibliografica: Optional[str] = None
    fecha_ingreso: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentoBibliotecaCreate(BaseModel):
    documento_id: int
    project_id: Optional[int] = None
    nombre: str
    tipo: str
    version: str
    filename: str
    usuario_id: str
    usuario_nombre: Optional[str] = None
    proyecto_nombre: Optional[str] = None
    descripcion: Optional[str] = None
    etiquetas: Optional[str] = None
