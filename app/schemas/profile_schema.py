from pydantic import BaseModel
from typing import Optional
from enum import Enum

class PrivacidadPerfilEnum(str, Enum):
    privado = "privado"
    publico = "publico"

class ProfileBase(BaseModel):
    nombre: Optional[str]
    apellidos: Optional[str]
    foto_url: Optional[str]
    direccion: Optional[str]
    ciudad: Optional[str]
    pais: Optional[str]
    cargo: Optional[str]
    empresa: Optional[str]
    biografia: Optional[str]
    linkedin: Optional[str]
    twitter: Optional[str]
    facebook: Optional[str]
    telefono: Optional[str]
    celular: Optional[str]
    intereses_interes_principal: Optional[str]
    intereses_formato_preferido: Optional[str]
    intereses_nivel_experiencia: Optional[str]
    intereses_objetivo_principal: Optional[str]
    notificaciones_email: Optional[bool] = True
    notificaciones_virtualmind: Optional[bool] = True
    privacidad_perfil: Optional[PrivacidadPerfilEnum] = PrivacidadPerfilEnum.privado

class ProfileCreate(ProfileBase):
    user_id: str

class ProfileOut(ProfileBase):
    user_id: str

    class Config:
        from_attributes = True

