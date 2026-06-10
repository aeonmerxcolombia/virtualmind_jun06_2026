from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.db import Base

class ArchivoCompartido(Base):
    __tablename__ = "archivos_compartidos"

    id = Column(Integer, primary_key=True, index=True)
    archivo_id = Column(Integer, ForeignKey("archivos.id", ondelete="CASCADE"), nullable=False)
    usuario_uid = Column(String(255), nullable=False) # El UID de quien recibe el archivo
    permiso = Column(String(50), default="lectura")
    fecha_compartido = Column(DateTime(timezone=True), server_default=func.now())

    # Relación para poder traer los datos del archivo fácilmente
    archivo = relationship("Archivo")
