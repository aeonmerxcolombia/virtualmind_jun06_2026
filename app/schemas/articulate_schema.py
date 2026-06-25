from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ==========================================
# ESQUEMAS PARA LAS DIAPOSITIVAS (SLIDES)
# ==========================================

class ArticulateSlideBase(BaseModel):
    tipo: str = Field(..., description="Tipo de componente: quiz, h5p, ace_code, etc.")
    # Usamos Dict[str, Any] para permitir la flexibilidad del JSON que enviará ACE Editor
    estado_json: Dict[str, Any] = Field(..., description="El estado y contenido del bloque interactivo")
    orden: Optional[int] = 0

class ArticulateSlideCreate(ArticulateSlideBase):
    project_id: str

class ArticulateSlideUpdate(BaseModel):
    tipo: Optional[str] = None
    estado_json: Optional[Dict[str, Any]] = None
    orden: Optional[int] = None

class ArticulateSlideResponse(ArticulateSlideBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        # Esto permite que Pydantic lea directamente los objetos de SQLAlchemy
        from_attributes = True 

# ==========================================
# ESQUEMAS PARA LOS PROYECTOS (PRESENTACIONES)
# ==========================================

class ArticulateProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ArticulateProjectCreate(ArticulateProjectBase):
    pass

class ArticulateProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class ArticulateProjectResponse(ArticulateProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    # Anidamos las diapositivas para que al pedir un proyecto, te devuelva todo el contenido armado
    slides: List[ArticulateSlideResponse] = []

    class Config:
        from_attributes = True
