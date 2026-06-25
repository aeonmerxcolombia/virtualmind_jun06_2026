from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.database.db import Base

class ContactMessage(Base):
    __tablename__ = "contacto_mensajes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    asunto = Column(String(255), nullable=False)
    mensaje = Column(Text, nullable=False)
    fecha_envio = Column(TIMESTAMP, server_default=func.now())

class Configuracion(Base):
    __tablename__ = "configuracion"

    clave = Column(String(50), primary_key=True)
    valor = Column(String(255), nullable=False)
    descripcion = Column(String(255), nullable=True)
