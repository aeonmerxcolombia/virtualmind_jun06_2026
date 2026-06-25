# app/models/folder.py

from sqlalchemy import (
    Column, Integer, String, Text,
    ForeignKey, TIMESTAMP, Boolean
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.db import Base

class Folder(Base):
    __tablename__ = "folders"

    id             = Column(Integer, primary_key=True, index=True)
    nombre         = Column(String(255), nullable=False)
    descripcion    = Column(Text)
    parent_id      = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=True)
    subido_por_uid = Column(String(255, collation="utf8mb4_unicode_ci"), ForeignKey("usuarios.uid", ondelete="SET NULL"), nullable=True)
    fecha_creado   = Column(TIMESTAMP, server_default=func.now())
    estado         = Column(Boolean, default=True)

    # Autorreferencia para subcarpetas
    padre    = relationship("Folder", remote_side=[id], back_populates="hijos")
    hijos    = relationship("Folder", back_populates="padre", cascade="all, delete-orphan")

    # Propietario de la carpeta
    uploader = relationship("User", back_populates="folders")

    # ¡NUEVO! Archivos contenidos en esta carpeta
    archivos = relationship("Archivo", back_populates="folder", cascade="all, delete-orphan")

