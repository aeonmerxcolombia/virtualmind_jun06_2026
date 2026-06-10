# app/models/audit_log.py

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base


class AuditLog(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_uid: Mapped[str] = mapped_column(String(255), ForeignKey("usuarios.uid", ondelete="CASCADE"), nullable=False, index=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    ciudad: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pais: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    latitud: Mapped[Optional[float]] = mapped_column(nullable=True)
    longitud: Mapped[Optional[float]] = mapped_column(nullable=True)
    fecha_entrada: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_salida: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duracion_segundos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    paginas_visitadas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", backref="audit_logs")
