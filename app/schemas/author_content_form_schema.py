# app/schemas/author_content_form_schema.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class AuthorContentFormBase(BaseModel):
    project_id: int
    course_name: str
    module_name: Optional[str] = None
    author_name: Optional[str] = None

    derechos_patrimoniales: Optional[bool] = False
    derechos_intelectuales: Optional[bool] = False

    publico_objetivo: Optional[str] = None
    horas_curso: Optional[int] = None
    horas_estudio_autonomo: Optional[int] = None
    horas_estudio_asincronico: Optional[int] = None

    indice_estructura: Optional[Dict[str, Any]] = None
    objetivos: Optional[Dict[str, Any]] = None
    contenido_escrito: Optional[Dict[str, Any]] = None
    narracion: Optional[Dict[str, Any]] = None
    estilo_narrativo: Optional[Dict[str, Any]] = None
    recursos_multimedia: Optional[Dict[str, Any]] = None
    actividades_aprendizaje: Optional[Dict[str, Any]] = None
    evaluacion: Optional[Dict[str, Any]] = None
    accesibilidad: Optional[Dict[str, Any]] = None
    referencias: Optional[str] = None
    glosario: Optional[List[Dict[str, Any]]] = None

class AuthorContentFormCreate(AuthorContentFormBase):
    pass

class AuthorContentFormUpdate(BaseModel):
    project_id: Optional[int] = None
    course_name: Optional[str] = None
    module_name: Optional[str] = None
    author_name: Optional[str] = None
    derechos_patrimoniales: Optional[bool] = None
    derechos_intelectuales: Optional[bool] = None
    publico_objetivo: Optional[str] = None
    horas_curso: Optional[int] = None
    horas_estudio_autonomo: Optional[int] = None
    horas_estudio_asincronico: Optional[int] = None
    indice_estructura: Optional[Dict[str, Any]] = None
    objetivos: Optional[Dict[str, Any]] = None
    contenido_escrito: Optional[Dict[str, Any]] = None
    narracion: Optional[Dict[str, Any]] = None
    estilo_narrativo: Optional[Dict[str, Any]] = None
    recursos_multimedia: Optional[Dict[str, Any]] = None
    actividades_aprendizaje: Optional[Dict[str, Any]] = None
    evaluacion: Optional[Dict[str, Any]] = None
    accesibilidad: Optional[Dict[str, Any]] = None
    referencias: Optional[str] = None
    glosario: Optional[List[Dict[str, Any]]] = None

class AuthorContentFormOut(AuthorContentFormBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

