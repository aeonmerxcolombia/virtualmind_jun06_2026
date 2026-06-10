from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LearningActivityBase(BaseModel):
    nombre: str = Field(..., example="Debate sobre ética en IA")
    descripcion: Optional[str] = Field(None, example="Discusión grupal sobre dilemas éticos en IA.")
    tipo: Optional[str] = Field(None, example="Debate")
    recursos: Optional[str] = Field(None, example="Enlace a lectura previa, videos, PDFs")

class LearningActivityCreate(LearningActivityBase):
    unit_id: int = Field(..., example=1)

class LearningActivityUpdate(BaseModel):
    nombre: Optional[str]
    descripcion: Optional[str]
    tipo: Optional[str]
    recursos: Optional[str]

class LearningActivityOut(LearningActivityBase):
    id: int
    unit_id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True

