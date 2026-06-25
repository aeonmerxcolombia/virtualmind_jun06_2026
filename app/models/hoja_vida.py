from sqlalchemy import Column, Integer, String, Text, JSON, TIMESTAMP, func, ForeignKey
from app.database.db import Base

class HojaVida(Base):
    __tablename__ = "hojas_vida"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("usuarios.uid"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    nombre_completo = Column(String(255))
    email = Column(String(255))
    telefono = Column(String(100))
    direccion = Column(Text)
    perfil_profesional = Column(Text)
    habilidades = Column(JSON)
    experiencia = Column(JSON)
    educacion = Column(JSON)
    idiomas = Column(JSON)
    certificaciones = Column(JSON)
    filename_original = Column(String(255))
    filename_almacenado = Column(String(255))
    ruta_archivo = Column(String(500))
    fecha_subida = Column(TIMESTAMP, server_default=func.now())
    fecha_actualizacion = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
