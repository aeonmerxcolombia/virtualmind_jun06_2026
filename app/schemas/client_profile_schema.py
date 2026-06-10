from pydantic import BaseModel, EmailStr
from typing import Optional

# --- CAMBIO: La clase base ahora contiene todos los nuevos campos del perfil ---
class ClientProfileBase(BaseModel):
    # --- DATOS DE LA ENTIDAD ---
    razon_social: Optional[str] = None
    nit: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    pais: Optional[str] = None
    caracter_entidad: Optional[str] = None
    tipo_entidad: Optional[str] = None
    tipo_entidad_otra: Optional[str] = None
    
    # --- DATOS DEL REPRESENTANTE LEGAL ---
    rep_legal_pnombre: Optional[str] = None
    rep_legal_snombre: Optional[str] = None
    rep_legal_papellido: Optional[str] = None
    rep_legal_sapellido: Optional[str] = None
    rep_legal_email: Optional[EmailStr] = None
    
    # --- DATOS INSTITUCIONALES ---
    email_institucional: Optional[EmailStr] = None
    telefono_institucional: Optional[str] = None
    whatsapp_institucional: Optional[str] = None
    email_adicional1: Optional[EmailStr] = None
    email_adicional2: Optional[EmailStr] = None

    # --- DATOS DEL CONTACTO COMERCIAL ---
    contacto_com_pnombre: Optional[str] = None
    contacto_com_snombre: Optional[str] = None
    contacto_com_papellido: Optional[str] = None
    contacto_com_sapellido: Optional[str] = None
    contacto_com_email: Optional[EmailStr] = None
    contacto_com_telefono: Optional[str] = None
    contacto_com_whatsapp: Optional[str] = None
    contacto_com_cargo: Optional[str] = None

    # --- DATOS DEL CONTACTO PRINCIPAL (USUARIO DE LA PLATAFORMA) ---
    pnombre: Optional[str] = None
    snombre: Optional[str] = None
    papellido: Optional[str] = None
    sapellido: Optional[str] = None
    cargo: Optional[str] = None
    
    # --- OBSERVACIONES ---
    observaciones: Optional[str] = None


# Esta clase se usa para crear un perfil, heredando los campos de la base
# y añadiendo el user_id necesario para la relación. No necesita cambios.
class ClientProfileCreate(ClientProfileBase):
    user_id: str


# Esta clase se usa para devolver un perfil desde la API.
# Hereda los nuevos campos de la base y añade id y user_id. No necesita cambios.
class ClientProfileOut(ClientProfileBase):
    id: str
    user_id: str

    class Config:
        from_attributes = True


class ClientProfileUpdate(ClientProfileBase):
    pass # Hereda todos los campos opcionales de ClientProfileBase
