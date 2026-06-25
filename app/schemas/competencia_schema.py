from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CompetenciaBase(BaseModel):
    habilidades: Optional[List[str]] = Field(default_factory=list)
    idiomas: Optional[List[str]] = Field(default_factory=list)
    nivel_academico: Optional[str] = None
    area_conocimiento: Optional[str] = None
    otros_estudios: Optional[str] = None
    anios_experiencia: Optional[int] = None
    perfilamiento: Optional[str] = None
    disponibilidad: Optional[str] = None

class CompetenciaCreate(CompetenciaBase):
    user_id: str  # <-- UUID como string

class CompetenciaUpdate(CompetenciaBase):
    pass

class CompetenciaOut(CompetenciaBase):
    id: str         # <-- UUID como string
    user_id: str    # <-- UUID como string
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

