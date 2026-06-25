from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.db import Base 

class ArticulateSlide(Base):
    __tablename__ = "articulate_slides"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String(36), ForeignKey("articulate_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    tipo = Column(String(100), nullable=False)
    estado_json = Column(JSON, nullable=False) 
    orden = Column(Integer, default=0) 
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("ArticulateProject", back_populates="slides")
