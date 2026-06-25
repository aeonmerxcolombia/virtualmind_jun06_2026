from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base
import enum

class EstadoVersion(str, enum.Enum):
    EN_PROGRESO = "en_progreso"
    EN_REVISION = "en_revision"
    APROBADA = "aprobada"
    CERRADA = "cerrada"

class DocumentoOficina(Base):
    __tablename__ = "documentos_office"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=True)
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False)
    filename = Column(String(255), nullable=False)
    ruta = Column(String(500), nullable=False)
    url_editar = Column(String(500), nullable=True)
    creado = Column(DateTime, server_default=func.now())
    actualizado = Column(DateTime, server_default=func.now(), onupdate=func.now())
    usuario_id = Column(String(255), nullable=False)

    # === CAMPOS DE VERSIONADO ===
    version_actual = Column(String(20), default="1.0")
    estado_version = Column(String(50), default="en_progreso")

    project = relationship("Project", backref="documentos_office")
    versiones = relationship("DocumentoVersion", back_populates="documento", order_by="DocumentoVersion.version.desc()")


class DocumentoVersion(Base):
    __tablename__ = "documento_office_versiones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey("documentos_office.id"), nullable=False)
    version = Column(String(20), nullable=False)  # "1.0", "2.0", etc.
    estado = Column(String(50), default="en_progreso")
    archivo_filename = Column(String(500), nullable=False)
    creado_por = Column(String(255), nullable=False)
    comentarios = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_cierre = Column(DateTime, nullable=True)

    documento = relationship("DocumentoOficina", back_populates="versiones")

class DocumentoOficinaCompartido(Base):
    __tablename__ = "documento_office_compartidos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey("documentos_office.id"), nullable=False)
    email_destino = Column(String(255), nullable=False)
    permiso = Column(String(50), default="lectura")
    fecha_compartido = Column(DateTime, server_default=func.now())
    
    documento = relationship("DocumentoOficina", backref="compartidos")

class DocumentoRevision(Base):
    __tablename__ = "documento_revisiones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(Integer, ForeignKey("documentos_office.id"), nullable=False)
    version = Column(String(20), nullable=False)
    autor_id = Column(String(255), nullable=False)
    coordinador_id = Column(String(255), nullable=True)
    cliente_id = Column(String(255), nullable=True)
    estado = Column(String(50), default="pendiente")  # pendiente, aprobado, devuelto, enviado_cliente
    comentarios = Column(Text, nullable=True)
    fecha_envio = Column(DateTime, server_default=func.now())
    fecha_respuesta = Column(DateTime, nullable=True)
    coordinador_visto = Column(DateTime, nullable=True)
    cliente_visto = Column(DateTime, nullable=True)

    documento = relationship("DocumentoOficina", backref="revisiones")
