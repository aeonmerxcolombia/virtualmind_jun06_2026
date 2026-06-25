from sqlalchemy import Column, Integer, String, DateTime, Date, Text, func
from app.database.db import Base

class SolicitudPieza(Base):
    __tablename__ = "solicitudes_pieza"

    id = Column(Integer, primary_key=True, index=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    solicitante = Column(String(100), nullable=False)
    destinatario = Column(String(100), nullable=False)
    tipo_solicitud = Column(String(50), nullable=False)
    fecha_maxima = Column(Date, nullable=False)
    fecha_entrega = Column(Date, nullable=True)
    proyecto = Column(String(100), nullable=False)
    curso = Column(String(100), nullable=True)
    modulo = Column(String(100), nullable=True)
    unidad = Column(String(100), nullable=True)
    tipo_animacion = Column(String(50), nullable=True)
    utilidad_animacion = Column(String(50), nullable=True)
    otro_utilidad = Column(String(100), nullable=True)
    nombre_pieza = Column(String(100), nullable=True)
    tamano = Column(String(50), nullable=True)
    descripcion = Column(Text, nullable=True)
    texto_infografia = Column(Text, nullable=True)
    voz_off = Column(String(50), nullable=True)
    enlace = Column(String(200), nullable=True)
    comentarios = Column(Text, nullable=True)

