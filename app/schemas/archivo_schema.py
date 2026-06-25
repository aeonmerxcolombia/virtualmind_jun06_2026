# app/schemas/archivo_schema.py

from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

# ==========================================
# LO QUE TÚ YA TENÍAS (NO SE TOCA)
# ==========================================
class ArchivoCreate(BaseModel):
    nombre_archivo: str
    url: HttpUrl
    tipo: Optional[str]
    folder_id: Optional[int]  # <-- carpeta donde se sube

class ArchivoOut(BaseModel):
    id: int
    nombre_archivo: str
    url: HttpUrl
    tipo: Optional[str]
    subido_por_uid: Optional[str]
    folder_id: Optional[int]      # <-- ahora lo devolvemos
    fecha_subida: datetime

    class Config:
        from_attributes = True

# ==========================================
# LO NUEVO QUE AGREGAMOS PARA COMPARTIR
# ==========================================
class CompartirRequest(BaseModel):
    email_invitado: str
    permiso: str = "lectura" # o "edicion"
    mensaje: Optional[str] = ""

class ArchivoCompartidoOut(BaseModel):
    id: int
    archivo_id: int
    usuario_uid: str
    permiso: str
    fecha_compartido: datetime
    # Anidamos tu ArchivoOut para que el frontend pueda pintar los datos del archivo
    archivo: ArchivoOut
    propietario_email: str
    
    class Config:
        from_attributes = True # En Pydantic v2 se usa from_attributes en lugar de orm_mode
