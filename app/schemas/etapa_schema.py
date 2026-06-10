# app/schemas/etapa_schema.py
from __future__ import annotations
from typing import List, Optional # <-- Asegúrate de tener List

from pydantic import BaseModel, Field
# Si en algún endpoint quieres devolver la fase completa, descomenta la línea siguiente:
# from .fase_schema import FaseRead


class EtapaBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    descripcion: Optional[str] = Field(None, max_length=500)
    orden: int = Field(default=0) # <-- Campo orden agregado
    fase_id: int


class EtapaCreate(EtapaBase):
    """Payload para POST /etapas"""
    # Si no quieres que 'orden' sea requerido al crear, puedes omitirlo
    # o dejar el valor por defecto del modelo de SQLAlchemy
    pass


class EtapaUpdate(BaseModel):
    """Payload para PUT /etapas/{id} (campos opcionales)"""
    nombre: Optional[str] = Field(None, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=500)
    orden: Optional[int] = Field(None) # <-- Campo orden agregado como opcional
    fase_id: Optional[int] = None

# ----------------------------------------------------------------------
#  Schema para reordenamiento
# ----------------------------------------------------------------------
class ReorderRequest(BaseModel):
    """Esquema para la solicitud de reordenamiento de etapas"""
    ids: List[int] # Lista de IDs de etapas en el nuevo orden

class EtapaRead(EtapaBase):
    """Respuesta para GET /etapas/{id}"""
    id: int
    # Si deseas incluir la fase completa, agrega:
    # fase: FaseRead | None = None   # opcional
    class Config:
        from_attributes = True

