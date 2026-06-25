# app/models/client_profile.py

# Se importa 'TYPE_CHECKING' para manejar la importación condicional
# del tipo, una práctica recomendada y muy limpia.
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.db import Base

# Esta construcción evita la importación circular en tiempo de ejecución
# pero permite que las herramientas de análisis de tipo (como mypy) funcionen.
if TYPE_CHECKING:
    from .user import User


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("usuarios.uid"), unique=True, nullable=False)

    # --- DATOS DE LA ENTIDAD (ACTUALIZADOS) ---
    razon_social: Mapped[Optional[str]] = mapped_column(String(255))
    nit: Mapped[Optional[str]] = mapped_column(String(50))
    tipo_entidad: Mapped[Optional[str]] = mapped_column(String(100))
    tipo_entidad_otra: Mapped[Optional[str]] = mapped_column(String(255))
    caracter_entidad: Mapped[Optional[str]] = mapped_column(String(50))
    direccion: Mapped[Optional[str]] = mapped_column(String(255))
    ciudad: Mapped[Optional[str]] = mapped_column(String(100))
    pais: Mapped[Optional[str]] = mapped_column(String(100))
    
    # --- DATOS DEL REPRESENTANTE LEGAL ---
    rep_legal_pnombre: Mapped[Optional[str]] = mapped_column(String(255))
    rep_legal_snombre: Mapped[Optional[str]] = mapped_column(String(255))
    rep_legal_papellido: Mapped[Optional[str]] = mapped_column(String(255))
    rep_legal_sapellido: Mapped[Optional[str]] = mapped_column(String(255))
    rep_legal_email: Mapped[Optional[str]] = mapped_column(String(255))

    # --- DATOS INSTITUCIONALES ---
    email_institucional: Mapped[Optional[str]] = mapped_column(String(255))
    telefono_institucional: Mapped[Optional[str]] = mapped_column(String(50))
    whatsapp_institucional: Mapped[Optional[str]] = mapped_column(String(50))
    email_adicional1: Mapped[Optional[str]] = mapped_column(String(255))
    email_adicional2: Mapped[Optional[str]] = mapped_column(String(255))

    # --- DATOS DEL CONTACTO COMERCIAL ---
    contacto_com_pnombre: Mapped[Optional[str]] = mapped_column(String(255))
    contacto_com_snombre: Mapped[Optional[str]] = mapped_column(String(255))
    contacto_com_papellido: Mapped[Optional[str]] = mapped_column(String(255))
    contacto_com_sapellido: Mapped[Optional[str]] = mapped_column(String(255))
    contacto_com_email: Mapped[Optional[str]] = mapped_column(String(255))
    contacto_com_telefono: Mapped[Optional[str]] = mapped_column(String(50))
    contacto_com_whatsapp: Mapped[Optional[str]] = mapped_column(String(50))
    contacto_com_cargo: Mapped[Optional[str]] = mapped_column(String(255))

    # --- DATOS DEL CONTACTO PRINCIPAL (USUARIO DE LA PLATAFORMA) ---
    pnombre: Mapped[Optional[str]] = mapped_column(String(255))
    snombre: Mapped[Optional[str]] = mapped_column(String(255))
    papellido: Mapped[Optional[str]] = mapped_column(String(255))
    sapellido: Mapped[Optional[str]] = mapped_column(String(255))
    cargo: Mapped[Optional[str]] = mapped_column(String(255))
    
    # --- OBSERVACIONES ---
    observaciones: Mapped[Optional[str]] = mapped_column(Text)

    # La relación con la tabla 'usuarios' se mantiene igual
    user: Mapped["User"] = relationship(
        "User",
        back_populates="client_profile"
    )
