# app/models/client_document.py

# Importaciones adicionales para el tipado moderno y robusto
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.db import Base

# Para manejar la referencia de tipo 'User' y evitar importaciones circulares
if TYPE_CHECKING:
    from .user import User


class ClientDocument(Base):
    __tablename__ = "client_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # --- MEJORA IMPORTANTE AQUÍ ---
    # La longitud de la ForeignKey (String(255)) ahora coincide con la de User.uid.
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("usuarios.uid"), nullable=False)
    
    tipo_documento: Mapped[str] = mapped_column(String(100), nullable=False)
    archivo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_subida: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

    # ===== CAMBIO FINAL AQUÍ =====
    # Se reemplaza backref por back_populates para una relación explícita y sin conflictos.
    user: Mapped["User"] = relationship(
        "User",
        back_populates="client_documents"
    )
