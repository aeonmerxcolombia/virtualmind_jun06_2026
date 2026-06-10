from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.database.db import Base

class Mensaje(Base):
    __tablename__ = "mensajes"

    id                = Column(String(36), primary_key=True, index=True)
    contenido         = Column(Text, nullable=False)
    remitente_uid     = Column(String(255), nullable=False)
    destinatario_uid  = Column(String(255), nullable=False)
    timestamp         = Column(TIMESTAMP, server_default=func.now())

