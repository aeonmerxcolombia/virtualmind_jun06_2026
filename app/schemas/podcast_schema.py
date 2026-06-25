# app/schemas/podcast_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PodcastBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    archivo_url: str
    tipo: Optional[str] = None
    subido_por: Optional[str] = None
    duracion_segundos: Optional[int] = None

class PodcastCreate(PodcastBase):
    pass  # para cuando recibes datos para crear (sin id ni fecha)

class PodcastOut(PodcastBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

