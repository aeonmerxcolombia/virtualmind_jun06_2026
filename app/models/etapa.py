# app/models/etapa.py
from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer # <-- Agregamos Integer
from sqlalchemy.orm import relationship
from app.database.db import Base


class Etapa(Base):
    __tablename__ = "etapas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(500), nullable=True)
    orden = Column(Integer, nullable=False, default=0) # <-- Campo orden agregado
    fase_id = Column(
        BigInteger,
        ForeignKey("fases.id"),
        nullable=False,
        index=True
    )

    # Cada etapa pertenece a una única fase
    fase = relationship("Fase", back_populates="etapas")
    tareas = relationship("Tarea", back_populates="etapa", cascade="all, delete-orphan")

