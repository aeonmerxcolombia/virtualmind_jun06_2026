from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func
from app.database.db import Base

class LogAccion(Base):
    __tablename__ = "logs_acciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer)
    tipo_evento = Column(String(100))
    descripcion = Column(Text)
    link = Column(String(500), nullable=True)  # URL a donde lleva la notificación
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    leido = Column(Boolean, default=False)

