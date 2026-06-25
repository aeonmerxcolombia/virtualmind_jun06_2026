from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class EvaluacionBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = ""
    fecha_limite: Optional[datetime]
    tipos_pregunta: List[str] = Field(..., example=["opcion_multiple", "abierta"])
    parametros: Optional[Dict[str, Any]] = {}
    generada_ia: int

class EvaluacionCreate(EvaluacionBase):
    creador_id: UUID

class EvaluacionOut(EvaluacionBase):
    id: UUID
    fecha_creacion: datetime
    generada_ia: int
    creador_id: UUID

    class Config:
        from_attributes = True

