from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.db import Base

class LearningActivity(Base):
    __tablename__ = "learning_activities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    unit_id = Column(BigInteger, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    tipo = Column(String(100))
    recursos = Column(Text)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())

    unit = relationship("Unit", back_populates="learning_activities")

