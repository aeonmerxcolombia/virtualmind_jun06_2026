# app/models/resource.py

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base
import enum

# 🔹 Enum para tipos de recurso
class ResourceType(enum.Enum):
    pdf = "pdf"
    image = "image"
    video = "video"
    audio = "audio"
    model = "model"

# 🔹 Enum para categorías (como Pixabay)
class ResourceCategory(enum.Enum):
    fotos = "fotos"
    ilustraciones = "ilustraciones"
    vectores = "vectores"
    videos = "videos"
    audios = "audios"
    documentos = "documentos"

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    file_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    file_type = Column(Enum(ResourceType), nullable=False)
    category = Column(Enum(ResourceCategory), nullable=True)
    tags = Column(String, nullable=True)
    owner_id = Column(String(255), ForeignKey("usuarios.uid"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación con usuarios (opcional, solo si definiste User)
    owner = relationship("User", back_populates="resources", lazy="joined")

