from pydantic import BaseModel
from datetime import datetime

class MensajeCreate(BaseModel):
    contenido: str
    destinatario_uid: str

class MensajeOut(BaseModel):
    id: str
    contenido: str
    remitente_uid: str
    destinatario_uid: str
    timestamp: datetime

    class Config:
        from_atributes = True

