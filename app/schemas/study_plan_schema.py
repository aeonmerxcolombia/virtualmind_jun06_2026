# app/schemas/study_plan.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.module_schema import ModuleOut

class StudyPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    modalidad: Optional[str] = None
    modalidad_otro: Optional[str] = None
    sincronia: Optional[str] = None
    duracion: Optional[int] = None
    objetivo_general: Optional[str] = None
    objetivos_especificos: Optional[List[str]] = Field(default_factory=list)
    resultados_aprendizaje: Optional[str] = None
    horas_estudio: Optional[str] = None
    recursos_libros: Optional[str] = None
    recursos_articulos: Optional[str] = None
    recursos_materiales: Optional[str] = None
    evaluaciones_cuestionarios: Optional[str] = None
    evaluaciones_examenes: Optional[str] = None
    evaluaciones_tareas: Optional[str] = None

class StudyPlanCreate(StudyPlanBase):
    project_id: int

class StudyPlanUpdate(StudyPlanBase):
    pass

class StudyPlanOut(StudyPlanBase):
    id: int
    project_id: int
    ultima_actualizacion: Optional[datetime] = None
    modules: Optional[List[ModuleOut]] = Field(default_factory=list)

    class Config:
        from_attributes = True
