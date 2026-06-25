

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

# Se agregó JSON a la importación
from sqlalchemy import Column, String, Boolean, Table, ForeignKey, Integer, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from app.database.db import Base

# Tabla pivote usuario ↔ rol (sin cambios)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_uid", String(255), ForeignKey("usuarios.uid", ondelete="CASCADE")),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"))
)

class User(Base):
    __tablename__ = "usuarios"

    uid: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_documento: Mapped[str] = mapped_column(String(50), nullable=False)
    documento: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, default=True)
    terms_accepted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP, nullable=True, default=None
    )
    
    # ===== NUEVO CAMPO: Biometría Facial =====
    face_embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # ===== NUEVO CAMPO: Biometría de Voz =====
    voice_embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # ===== Campo para estado de presencia =====
    last_seen: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, default=None)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relaciones originales (intactas)
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users"
    )

    folders: Mapped[List["Folder"]] = relationship(
        "Folder",
        back_populates="uploader",
        cascade="all, delete-orphan"
    )

    archivos: Mapped[List["Archivo"]] = relationship(
        "Archivo",
        back_populates="uploader",
        cascade="all, delete-orphan"
    )

    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        back_populates="user"
    )

    client_profile: Mapped[Optional["ClientProfile"]] = relationship(
        "ClientProfile",
        back_populates="user",
        cascade="all, delete-orphan" 
    )

    client_documents: Mapped[List["ClientDocument"]] = relationship(
        "ClientDocument",
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    resources = relationship("Resource", back_populates="owner")
