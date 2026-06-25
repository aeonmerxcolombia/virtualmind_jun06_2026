from sqlalchemy import Column, String, ForeignKey, Boolean, Text, Enum, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base
import enum

class PrivacidadPerfilEnum(enum.Enum):
    privado = "privado"
    publico = "publico"

class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(String(36), ForeignKey("usuarios.uid"), primary_key=True, nullable=False)
    nombre = Column(String(255))
    apellidos = Column(String(255))
    foto_url = Column(String(255))
    direccion = Column(String(255))
    ciudad = Column(String(100))
    pais = Column(String(100))
    cargo = Column(String(255))
    empresa = Column(String(255))
    biografia = Column(Text)
    linkedin = Column(String(255))
    twitter = Column(String(255))
    facebook = Column(String(255))
    telefono = Column(String(50))
    celular = Column(String(50))
    intereses_interes_principal = Column(String(100))
    intereses_formato_preferido = Column(String(50))
    intereses_nivel_experiencia = Column(String(50))
    intereses_objetivo_principal = Column(String(100))
    intereses_temas = Column(Text)
    notificaciones_email = Column(Boolean, default=True)
    notificaciones_virtualmind = Column(Boolean, default=True)
    privacidad_perfil = Column(Enum(PrivacidadPerfilEnum), default=PrivacidadPerfilEnum.privado)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    ultima_actualizacion = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")

