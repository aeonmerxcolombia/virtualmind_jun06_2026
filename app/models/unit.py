# app/models/unit.py

from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.db import Base

class Unit(Base):
    __tablename__ = "units"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Información básica y heredada
    name = Column(String(255), nullable=False, comment="Nombre de la unidad")
    short_name = Column(String(255), nullable=False, comment="Nombre corto de la Unidad")
    unit_code = Column(String(100), nullable=True, comment="Código / ID de la unidad (Heredado del modulo)")
    
    # Objetivos
    general_objective = Column(Text, nullable=False, comment="Objetivo general de la unidad")
    specific_objectives = Column(Text, nullable=True, comment="Objetivos específicos de la unidad (Heredan del Modulo segun escrito de autoria)")
    
    # Contenido y duración
    duration = Column(String(100), nullable=True, comment="Duración estimada (min/horas) (Esta dentro del rango de tiempo del modulo...)")
    contents = Column(Text, nullable=True, comment="Contenidos / sub temas incluidos (Estan en el escrito de contenidos)")
    
    # Recursos
    multimedia_resources = Column(Text, nullable=True, comment="Recursos multimedia (Los mismos del modulo, colocar cada tipo de formato)")
    
    # Actividades
    has_activities = Column(Boolean, nullable=False, default=True, comment="Indica presencia de actividades (minimo una por unidad)")
    activity_types = Column(Text, nullable=True, comment="Tipo de actividades (Las mismas del modulo)")
    activity_instructions = Column(Text, nullable=True, comment="Instrucciones de actividades (Las mismas del modulo)")
    
    # Evaluación y otros
    has_downloadable_materials = Column(Boolean, nullable=False, default=False, comment="Materiales descargables (Si o no)")
    has_assessment = Column(Boolean, nullable=False, default=False, comment="Evaluación asociada a la unidad (Si o no)")
    accessibility = Column(Text, nullable=True, comment="Accesibilidad")
    additional_notes = Column(Text, nullable=True, comment="Notas adicionales")
    
    # Relación con el módulo
    module_id = Column(BigInteger, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, comment="ID del módulo al que pertenece esta unidad")

    # Relaciones
    module = relationship("Module", back_populates="units")
    learning_activities = relationship("LearningActivity", back_populates="unit", cascade="all, delete-orphan")

