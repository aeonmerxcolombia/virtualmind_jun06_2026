from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClientDocumentBase(BaseModel):
    tipo_documento: str
    archivo_url: str

class ClientDocumentCreate(ClientDocumentBase):
    user_id: str

class ClientDocumentOut(ClientDocumentBase):
    id: str
    user_id: str
    fecha_subida: datetime

    class Config:
        from_attributes = True

