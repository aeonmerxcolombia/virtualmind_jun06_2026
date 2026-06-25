# app/models/fase.py
from sqlalchemy import Column, BigInteger, String, Integer # <-- Agregamos Integer
from sqlalchemy.orm import relationship
from app.database.db import Base


class Fase(Base):
    __tablename__ = "fases"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(500), nullable=True)
    orden = Column(Integer, nullable=False, default=0) # <-- Campo orden agregado

    # Una fase → muchas etapas
    # Se usa el nombre de la clase como string para evitar importaciones circulares
    etapas = relationship(
        "Etapa",
        back_populates="fase",
        cascade="all, delete-orphan",
        order_by="Etapa.orden" # <-- Ordenar etapas por el campo 'orden' por defecto
    )

    proyectos = relationship(
        "Project",                 # nombre del modelo que apunta a esta tabla
        back_populates="fase",    # debe coincidir con `back_populates` en Project
        cascade="all, delete-orphan"
    )
    tareas = relationship("Tarea", back_populates="fase", cascade="all, delete-orphan")

