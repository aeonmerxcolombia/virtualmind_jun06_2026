from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

# --- Esquemas para la estructura JSON anidada ---
class Etapa(BaseModel):
    etapa_id: int
    nombre_etapa: str
    fecha_inicio: date
    fecha_fin: date
    estado: str
    responsables: List[str]

class Fase(BaseModel):
    fase_id: int
    nombre_fase: str
    fecha_inicio: date
    fecha_fin: date
    estado: str
    etapas: List[Etapa]

# --- Esquemas Principales del Cronograma ---
class CronogramaBase(BaseModel):
    nombre: Optional[str] = None
    estado: Optional[str] = 'planificado'
    estructura: Optional[List[Fase]] = None

    model_config = ConfigDict(
        json_encoders={
            date: lambda v: v.isoformat(),
        }
    )

class CronogramaCreate(CronogramaBase):
    project_id: int

class CronogramaUpdate(CronogramaBase):
    pass

# --- Esquema para Leer/Mostrar un Cronograma ---
class CronogramaRead(CronogramaBase):
    id: int
    project_id: int
    created_at: datetime
    # =================================================================
    # CORRECCIÓN: Permitir que updated_at sea nulo en la respuesta
    # =================================================================
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


