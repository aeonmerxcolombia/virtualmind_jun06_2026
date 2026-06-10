# app/schemas/client_schema.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from .client_profile_schema import ClientProfileBase

class FullClientCreate(BaseModel):
    # --- CAMBIO AQUÍ ---
    # Añadido el campo 'nombre', que es obligatorio en el modelo User
    nombre: str

    # Datos para la tabla 'usuarios'
    email: EmailStr
    password: Optional[str] = None
    tipo_documento: str
    documento: str

    # Todos los datos del perfil vienen anidados en un solo objeto
    profile: ClientProfileBase
