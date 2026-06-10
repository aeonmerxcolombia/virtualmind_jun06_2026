# app/schemas/user_schema.py

from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime  # <--- IMPORTACIÓN AÑADIDA

class UserCreate(BaseModel):
    nombre: str
    tipo_documento: str
    documento: str
    email: EmailStr
    password: str
    role_ids: List[int]        # IDs de roles que vienen en la petición

class UserOut(BaseModel):
    uid: str
    nombre: str
    tipo_documento: str
    documento: str
    email: EmailStr
    roles: List[str]           # Aquí devolvemos sólo los nombres
    estado: bool

    # --- CAMPO AÑADIDO (con la fecha) ---
    terms_accepted_at: Optional[datetime] = None

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

class UserStatusUpdate(BaseModel):
    """
    Esquema específico y seguro para recibir solo la actualización del estado.
    """
    estado: bool

# --- ESQUEMAS AÑADIDOS PARA LOGIN Y JWT ---

class Token(BaseModel):
    """
    Esquema para la RESPUESTA del endpoint de Login (/token o /login).
    """
    access_token: str
    token_type: str
    # Este es el booleano 'derivado' para el frontend
    terms_accepted: bool 

class TokenData(BaseModel):
    """
    Esquema para validar los datos DENTRO del JWT.
    (Basado en tu verify_token, parece que guardas 'user_id' (uid) en el token)
    """
    user_id: Optional[str] = None

class UserEmailUpdate(BaseModel):
    """
    Schema to receive only the new email address for an update.
    """
    email: EmailStr # Ensures the input is a valid email format
