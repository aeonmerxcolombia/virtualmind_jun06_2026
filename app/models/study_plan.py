# app/models/study_plan.py

from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    modalidad = Column(String(100))
    modalidad_otro = Column(String(100))
    sincronia = Column(String(50))
    duracion = Column(Integer)
    objetivo_general = Column(Text)
    objetivos_especificos = Column(Text)
    resultados_aprendizaje = Column(Text)
    horas_estudio = Column(String(100))
    recursos_libros = Column(Text)
    recursos_articulos = Column(Text)
    recursos_materiales = Column(Text)
    evaluaciones_cuestionarios = Column(Text)
    evaluaciones_examenes = Column(Text)
    evaluaciones_tareas = Column(Text)
    ultima_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ✅ Relación con módulos (antes era con cursos)
    modules = relationship("Module", back_populates="study_plan", cascade="all, delete-orphan")

