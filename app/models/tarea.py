import json
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, BigInteger, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.db import Base

class Tarea(Base):
    __tablename__ = "tareas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_inicio = Column(Date, nullable=True)
    fecha_entrega = Column(Date, nullable=True)
    estado = Column(String(50), nullable=True)
    prioridad = Column(String(50), nullable=True)
    asignado = Column(String(255), nullable=True)
    seguidores = Column(Text, nullable=True)
    adjuntos = Column(Text, nullable=True)
    creado_por = Column(String(255), nullable=True)
    
    fase_id = Column(BigInteger, ForeignKey("fases.id"), nullable=False)
    etapa_id = Column(BigInteger, ForeignKey("etapas.id"), nullable=False)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False)
    
    # Timestamps
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="tareas")
    fase = relationship("Fase", back_populates="tareas")
    etapa = relationship("Etapa", back_populates="tareas")
    
    # ---- Propiedades JSON → lista
    @property
    def seguidores_list(self):
        try:
            return json.loads(self.seguidores) if self.seguidores else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    @property
    def adjuntos_list(self):
        try:
            return json.loads(self.adjuntos) if self.adjuntos else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    # ---- Setters lista → JSON
    @seguidores_list.setter
    def seguidores_list(self, value):
        self.seguidores = json.dumps(value) if value else None
    
    @adjuntos_list.setter
    def adjuntos_list(self, value):
        self.adjuntos = json.dumps(value) if value else None
    
    def __repr__(self):
        return f"<Tarea(id={self.id}, titulo='{self.titulo}', project_id={self.project_id})>"
