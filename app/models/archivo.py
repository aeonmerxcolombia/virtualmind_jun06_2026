# app/models/archivo.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.db import Base

class Archivo(Base):
    __tablename__ = "archivos"

    id              = Column(Integer, primary_key=True, index=True)
    nombre_archivo  = Column(String(255), nullable=False)
    url             = Column(Text, nullable=False)
    tipo            = Column(String(50), nullable=True)

    # FK al usuario que sube
    subido_por_uid  = Column(
        String(255, collation="utf8mb4_unicode_ci"),
        ForeignKey("usuarios.uid", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # ¡NUEVO! FK a carpetas
    folder_id       = Column(
        Integer,
        ForeignKey("folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    fecha_subida    = Column(TIMESTAMP, server_default=func.now())

    # Relaciones
    uploader = relationship("User",   back_populates="archivos")
    folder   = relationship("Folder", back_populates="archivos")

