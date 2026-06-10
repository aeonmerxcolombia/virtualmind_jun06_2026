from typing import List, Optional
from pydantic import BaseModel, validator
from datetime import date, datetime
import json

class TareaBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_entrega: Optional[date] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    asignado: Optional[str] = None
    seguidores: List[str] = []
    adjuntos: List[str] = []
    fase_id: Optional[int] = None
    etapa_id: Optional[int] = None
    project_id: int
    
    # --- Validadores para convertir string JSON a lista ---
    @validator("seguidores", pre=True)
    def parse_seguidores(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v
    
    @validator("adjuntos", pre=True)
    def parse_adjuntos(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_entrega: Optional[date] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    asignado: Optional[str] = None
    seguidores: Optional[List[str]] = None
    adjuntos: Optional[List[str]] = None
    fase_id: Optional[int] = None
    etapa_id: Optional[int] = None
    project_id: Optional[int] = None
    
    # --- Validadores para convertir string JSON a lista ---
    @validator("seguidores", pre=True)
    def parse_seguidores(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v
    
    @validator("adjuntos", pre=True)
    def parse_adjuntos(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v

class TareaOut(TareaBase):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    class Config:
        from_attributes = True
