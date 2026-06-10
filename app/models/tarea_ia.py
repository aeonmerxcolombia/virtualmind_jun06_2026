from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database.db import Base

class TareaIA(Base):
    __tablename__ = "tareas_ia"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    descripcion = Column(Text, nullable=False)
    prioridad = Column(String(20), default="medium")
    categoria = Column(String(50), default="other")
    estado = Column(String(20), default="pending")
    responsable = Column(String(20), default="backend")  # qa, frontend, backend
    notas = Column(Text, nullable=True)
    
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<TareaIA(id={self.id}, descripcion='{self.descripcion[:30]}...', estado='{self.estado}', responsable='{self.responsable}')>"
