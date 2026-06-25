from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, ForeignKey
from sqlalchemy.sql import func
from app.database.db import Base


class DocumentoBiblioteca(Base):
    __tablename__ = "documentos_biblioteca"

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, nullable=False)
    project_id = Column(BigInteger, nullable=True)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)
    filename = Column(String(500), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    usuario_id = Column(String(255), nullable=False)
    usuario_nombre = Column(String(255), nullable=True)
    proyecto_nombre = Column(String(255), nullable=True)
    descripcion = Column(Text, nullable=True)
    etiquetas = Column(String(500), nullable=True)
    nota_bibliografica = Column(Text, nullable=True)
    fecha_ingreso = Column(DateTime, server_default=func.now())


class AccesoBiblioteca(Base):
    __tablename__ = "accesos_biblioteca"

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey("documentos_biblioteca.id"), nullable=False)
    usuario_id = Column(String(255), nullable=True)
    rol = Column(String(50), nullable=True)
    permiso = Column(String(50), default="lectura")
    fecha_asignado = Column(DateTime, server_default=func.now())


class SolicitudAccesoBiblioteca(Base):
    __tablename__ = "solicitudes_acceso_biblioteca"

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey("documentos_biblioteca.id"), nullable=False)
    solicitante_id = Column(String(255), nullable=False)
    solicitante_nombre = Column(String(255), nullable=True)
    razon = Column(Text, nullable=True)
    estado = Column(String(50), default="pendiente")
    respuesta_admin = Column(Text, nullable=True)
    fecha_solicitud = Column(DateTime, server_default=func.now())
    fecha_resolucion = Column(DateTime, nullable=True)
    resuelto_por = Column(String(255), nullable=True)
