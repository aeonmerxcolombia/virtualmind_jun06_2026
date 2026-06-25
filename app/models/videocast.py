from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database.db import Base

class Videocast(Base):
    __tablename__ = "videocasts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    archivo_url = Column(String(500), nullable=False)
    tipo = Column(String(50), nullable=True)
    subido_por = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
