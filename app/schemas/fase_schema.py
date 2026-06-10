# app/schemas/fase_schema.py
from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel, Field # <-- Asegúrate de tener esta importación


# ----------------------------------------------------------------------
#  Base – campos comunes (uso interno)
# ----------------------------------------------------------------------
class FaseBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    descripcion: Optional[str] = Field(None, max_length=500)
    orden: int = Field(default=0) # <-- Campo orden agregado


# ----------------------------------------------------------------------
#  Schemas de entrada (POST/PUT)
# ----------------------------------------------------------------------
class FaseCreate(FaseBase):
    """Payload para crear una fase (POST /fases)"""
    # Si no quieres que 'orden' sea requerido al crear, puedes omitirlo
    # o dejar el valor por defecto del modelo de SQLAlchemy
    pass


class FaseUpdate(BaseModel):
    """Payload para actualizar parcialmente (PUT /fases/{id})"""
    nombre: Optional[str] = Field(None, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=500)
    orden: Optional[int] = Field(None) # <-- Campo orden agregado como opcional

# ----------------------------------------------------------------------
#  Schema para reordenamiento
# ----------------------------------------------------------------------
class ReorderRequest(BaseModel):
    """Esquema para la solicitud de reordenamiento de fases"""
    ids: List[int] # Lista de IDs de fases en el nuevo orden

# ----------------------------------------------------------------------
#  Schema de salida (GET)
# ----------------------------------------------------------------------
class EtapaRead(BaseModel):
    """Representación mínima de una Etapa para incluirla dentro de FaseRead.
    La definición completa la tendrás en `etapa_schema.py`; aquí solo
    declaramos los campos que necesitamos para evitar importaciones circulares."""
    id: int
    nombre: str
    descripcion: Optional[str] = None
    orden: int # <-- Campo orden agregado
    fase_id: int

    class Config:
        from_attributes = True


class FaseRead(FaseBase):
    """Respuesta para GET /fases/{id} (incluye sus etapas)"""
    id: int
    etapas: List[EtapaRead] = []   # lista de etapas relacionadas

    class Config:
        from_attributes = True

