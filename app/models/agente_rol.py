from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database.db import Base

class AgenteRol(Base):
    __tablename__ = "agentes_rol"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rol = Column(String(50), nullable=False, index=True)
    descripcion = Column(Text, nullable=False)
    prioridad = Column(String(20), default="medium")
    estado = Column(String(20), default="pending")
    user_email = Column(String(255), nullable=True)
    resultado = Column(Text, nullable=True)
    notas = Column(Text, nullable=True)

    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AgenteRol(id={self.id}, rol='{self.rol}', desc='{self.descripcion[:30]}...', estado='{self.estado}')>"
