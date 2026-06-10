# app/models/podcast.py

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.database.db import Base

class Podcast(Base):
    __tablename__ = "podcasts"

    id                = Column(Integer, primary_key=True, index=True)
    titulo            = Column(String(255), nullable=False)
    descripcion       = Column(Text, nullable=True)
    archivo_url       = Column(Text, nullable=False)
    tipo              = Column(String(50), nullable=True)
    fecha_creacion    = Column(TIMESTAMP, server_default=func.now())
    subido_por        = Column(String(100), nullable=True)
    duracion_segundos = Column(Integer, nullable=True)

