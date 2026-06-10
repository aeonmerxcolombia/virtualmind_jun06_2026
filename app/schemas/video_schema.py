from pydantic import BaseModel
from typing import Optional

class VideoSessionCreate(BaseModel):
    mi_uid: str  # Campo integrado para almacenar de forma segura el UID del creador en la base de datos
    mi_nombre: str
    mi_email: str
    destinatario_uid: str

class VideoSessionRead(BaseModel):
    url: str
    token: str
    room_name: str

    class Config:
        from_attributes = True  # Mapeo ORM para compatibilidad con los modelos de SQLAlchemy
