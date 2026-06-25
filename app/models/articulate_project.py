from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.db import Base 

class ArticulateProject(Base):
    __tablename__ = "articulate_projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    slides = relationship("ArticulateSlide", back_populates="project", cascade="all, delete-orphan")
