from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentoOfficeBase(BaseModel):
    nombre: str
    tipo: str
    project_id: Optional[int] = None # Agregamos el project_id

class DocumentoOfficeCreate(DocumentoOfficeBase):
    pass

class DocumentoOfficeOut(DocumentoOfficeBase):
    id: int
    filename: str
    ruta: str
    url_editar: Optional[str] = None
    creado: datetime
    actualizado: Optional[datetime] = None
    usuario_id: Optional[str] = None
    version_actual: Optional[str] = "1.0"
    estado_version: Optional[str] = "en_progreso"

    class Config:
        from_attributes = True
