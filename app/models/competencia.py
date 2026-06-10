from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.database.db import Base
import uuid

class Competencia(Base):
    __tablename__ = "competencias"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("usuarios.uid", ondelete="CASCADE"), nullable=False)

    habilidades = Column(JSON, nullable=False)
    idiomas = Column(JSON)
    nivel_academico = Column(String(50))
    area_conocimiento = Column(String(255))
    otros_estudios = Column(Text)
    anios_experiencia = Column(Integer)
    perfilamiento = Column(Text)
    disponibilidad = Column(Text)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

