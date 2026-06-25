from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class SolicitudPiezaBase(BaseModel):
    solicitante: str
    destinatario: str
    tipo_solicitud: str
    fecha_maxima: date
    proyecto: str
    curso: Optional[str]
    modulo: Optional[str]
    unidad: Optional[str]
    tipo_animacion: Optional[str]
    utilidad_animacion: Optional[str]
    otro_utilidad: Optional[str]
    nombre_pieza: Optional[str]
    tamano: Optional[str]
    descripcion: Optional[str]
    texto_infografia: Optional[str]
    voz_off: Optional[str]
    enlace: Optional[str]
    comentarios: Optional[str]

class SolicitudPiezaCreate(SolicitudPiezaBase):
    pass

class SolicitudPiezaOut(SolicitudPiezaBase):
    id: int
    fecha_creacion: datetime
    fecha_entrega: Optional[date]

    class Config:
        from_attributes = True

