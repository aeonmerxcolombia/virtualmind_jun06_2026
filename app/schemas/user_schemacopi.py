from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional

class UserCreate(BaseModel):
    nombre: str
    tipo_documento: str
    documento: str
    email: EmailStr
    password: str
    role_ids: List[int]       # IDs de roles que vienen en la petición

class UserOut(BaseModel):
    uid: str
    nombre: str
    tipo_documento: str
    documento: str
    email: EmailStr
    roles: List[str]          # Aquí devolvemos sólo los nombres
    estado: bool

    @validator("roles", pre=True)
    def extract_role_names(cls, v):
        # v es la lista de Role ORM; devolvemos sólo sus atributos .name
        return [rol.name for rol in v]

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    nombre: Optional[str]
    tipo_documento: Optional[str]
    documento: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    role_ids: Optional[List[int]]  # IDs de roles para actualizar
    estado: Optional[bool]

class UserDeleteResponse(BaseModel):
    msg: str
    uid: str

# --- AÑADE ESTA NUEVA CLASE AL FINAL DEL ARCHIVO ---
class UserStatusUpdate(BaseModel):
    """
    Esquema específico y seguro para recibir solo la actualización del estado.
    """
    estado: bool
