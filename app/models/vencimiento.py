from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.db import Base


class AlertaVencimiento(Base):
    __tablename__ = "alertas_vencimiento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tarea_id = Column(Integer, ForeignKey("tareas.id"), nullable=False)
    tipo = Column(String(50), default="recordatorio")
    enviado_a = Column(String(255), nullable=True)
    dias_antes = Column(Integer, default=2)
    fecha_envio = Column(DateTime, server_default=func.now())

    tarea = relationship("Tarea")


class SolicitudAmpliacion(Base):
    __tablename__ = "solicitudes_ampliacion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tarea_id = Column(Integer, ForeignKey("tareas.id"), nullable=False)
    usuario_id = Column(String(255), nullable=False)
    fecha_actual = Column(Date, nullable=False)
    fecha_solicitada = Column(Date, nullable=False)
    razon = Column(Text, nullable=False)
    estado = Column(String(50), default="pendiente")
    respuesta_admin = Column(Text, nullable=True)
    fecha_resolucion = Column(DateTime, nullable=True)
    resuelto_por = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now())

    tarea = relationship("Tarea")

    def __repr__(self):
        return f"<SolicitudAmpliacion(id={self.id}, tarea_id={self.tarea_id}, estado='{self.estado}')>"
