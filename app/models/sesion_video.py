from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from app.database.db import Base

class SesionVideo(Base):
    __tablename__ = "sesiones_video"

    id = Column(Integer, primary_key=True, index=True)
    room_name = Column(String(255), nullable=False, unique=True, index=True)
    creador_uid = Column(String(100), nullable=False, index=True)
    participante_uid = Column(String(100), nullable=False, index=True)
    status = Column(Enum('waiting', 'active', 'finished'), default='waiting')
    created_at = Column(DateTime, default=func.now())
