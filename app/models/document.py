from sqlalchemy import (
    Column, BigInteger, String, ForeignKey, Text, DateTime, func
)
from app.database.db import Base
from sqlalchemy.orm import relationship


class Document(Base):
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False)
    document_type = Column(String(255), nullable=False)
    document_name = Column(String(255), nullable=False)
    document_url = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    # Relación con el modelo Project
    project = relationship("Project", back_populates="documents")

