# app/models/evaluacion.py

from sqlalchemy import Column, String, Text, DateTime, JSON, CHAR, Integer
from sqlalchemy.sql import func
from app.database.db import Base

class Evaluacion(Base):
    __tablename__ = "evaluaciones"

    id = Column(CHAR(36), primary_key=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_limite = Column(DateTime, nullable=True)
    creador_id = Column(CHAR(36), nullable=False)
    tipos_pregunta = Column(JSON, nullable=False)  # Lista/objeto con tipos seleccionados
    parametros = Column(JSON)                      # Config extra, instrucciones, etc.
    generada_ia = Column(Integer, default=0)       # 1=generada por IA, 0=no
