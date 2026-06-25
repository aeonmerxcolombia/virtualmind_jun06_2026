from sqlalchemy import Column, BigInteger, String, ForeignKey, JSON, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base

class Cronograma(Base):
    __tablename__ = "cronogramas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), unique=True, nullable=False)

    nombre = Column(String(255), nullable=True)
    estructura = Column(JSON, nullable=True)
    estado = Column(String(25), nullable=False, server_default='planificado')
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # --- Relación ---
    # Nota: El back_populates probablemente deba ser "cronograma" (singular)
    # en tu modelo Project, ya que ahora es una relación uno-a-uno.
    project = relationship("Project", back_populates="cronograma")
