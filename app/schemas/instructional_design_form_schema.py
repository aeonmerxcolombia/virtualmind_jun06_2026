# app/schemas/instructional_design_form_schema.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class InstructionalDesignFormBase(BaseModel):
    project_id: int
    course_name: str
    module_name: Optional[str] = None
    unit_name: Optional[str] = None

    objetivo_instruccional: Optional[str] = None
    mensaje_clave: Optional[str] = None

    persona_narrativa: Optional[Dict[str, Any]] = None
    narrador_estilo: Optional[Dict[str, Any]] = None

    texto_pantalla_inicio: Optional[bool] = False
    voz_en_off: Optional[bool] = False

    recursos_visuales: Optional[List[Dict[str, Any]]] = None
    recursos_multimedia: Optional[Dict[str, Any]] = None
    interacciones: Optional[List[str]] = None
    actividades_aprendizaje: Optional[List[Dict[str, Any]]] = None

    feedback: Optional[str] = None
    evaluacion: Optional[Dict[str, Any]] = None
    accesibilidad: Optional[Dict[str, Any]] = None

    notas_productor: Optional[str] = None
    observaciones: Optional[str] = None

class InstructionalDesignFormCreate(InstructionalDesignFormBase):
    pass

class InstructionalDesignFormUpdate(BaseModel):
    course_name: Optional[str] = None
    module_name: Optional[str] = None
    unit_name: Optional[str] = None
    objetivo_instruccional: Optional[str] = None
    mensaje_clave: Optional[str] = None
    persona_narrativa: Optional[Dict[str, Any]] = None
    narrador_estilo: Optional[Dict[str, Any]] = None
    texto_pantalla_inicio: Optional[bool] = None
    voz_en_off: Optional[bool] = None
    recursos_visuales: Optional[List[Dict[str, Any]]] = None
    recursos_multimedia: Optional[Dict[str, Any]] = None
    interacciones: Optional[List[str]] = None
    actividades_aprendizaje: Optional[List[Dict[str, Any]]] = None
    feedback: Optional[str] = None
    evaluacion: Optional[Dict[str, Any]] = None
    accesibilidad: Optional[Dict[str, Any]] = None
    notas_productor: Optional[str] = None
    observaciones: Optional[str] = None

class InstructionalDesignFormOut(InstructionalDesignFormBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

