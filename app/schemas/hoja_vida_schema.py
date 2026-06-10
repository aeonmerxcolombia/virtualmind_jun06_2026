from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class HojaVidaBase(BaseModel):
    nombre_completo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    perfil_profesional: Optional[str] = None
    habilidades: Optional[List[str]] = None
    experiencia: Optional[List[dict]] = None
    educacion: Optional[List[dict]] = None
    idiomas: Optional[List[str]] = None
    certificaciones: Optional[List[str]] = None

class HojaVidaCreate(HojaVidaBase):
    project_id: Optional[int] = None

class HojaVidaUpdate(HojaVidaBase):
    pass

class HojaVidaOut(HojaVidaBase):
    id: int
    user_id: Optional[str] = None
    project_id: Optional[int] = None
    filename_original: Optional[str] = None
    filename_almacenado: Optional[str] = None
    fecha_subida: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True
