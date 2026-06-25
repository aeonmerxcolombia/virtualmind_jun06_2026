from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class ProjectBase(BaseModel):
    name: str
    client_id: str
    codigo_referencia: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    tipo_proyecto: Optional[str] = None
    tipo_proyecto_personalizado: Optional[str] = None
    estado: Optional[str] = "Planificado"
    description: Optional[str] = None

    fase_id: Optional[int] = None  # Nueva relación con Fase

    lenguaje_incluyente: Optional[bool] = False
    lenguaje_inclusivo_tipo: Optional[str] = None
    lenguaje_inclusivo_otro: Optional[str] = None

    inclusion_digital: Optional[bool] = False
    inclusion_digital_web: Optional[bool] = False
    inclusion_digital_asistiva: Optional[bool] = False
    inclusion_digital_universal: Optional[bool] = False
    inclusion_digital_educativa: Optional[bool] = False
    inclusion_digital_otro: Optional[str] = None

    idioma: Optional[str] = None
    idioma_otro: Optional[str] = None

    # Tipografía - Título
    tipografia_titulo_fuente: Optional[str] = None
    tipografia_titulo_tamano: Optional[str] = None
    tipografia_titulo_negrita: Optional[bool] = False
    tipografia_titulo_cursiva: Optional[bool] = False

    # Tipografía - Subtítulo
    tipografia_subtitulo_fuente: Optional[str] = None
    tipografia_subtitulo_tamano: Optional[str] = None
    tipografia_subtitulo_negrita: Optional[bool] = False
    tipografia_subtitulo_cursiva: Optional[bool] = False

    # Tipografía - Párrafo
    tipografia_parrafo_fuente: Optional[str] = None
    tipografia_parrafo_tamano: Optional[str] = None
    tipografia_parrafo_negrita: Optional[bool] = False
    tipografia_parrafo_cursiva: Optional[bool] = False

    horas_curso: Optional[float] = None

    diseno_grafico_tipo: Optional[str] = None
    diseno_grafico_paleta: Optional[str] = None

    cesion_derechos: Optional[bool] = False
    derechos_patrimoniales_autor: Optional[bool] = False
    acuerdo_confidencialidad: Optional[bool] = False
    entrega_fuentes: Optional[bool] = False
    entrega_escrito_autor: Optional[bool] = False
    entrega_diseno_instruccional: Optional[bool] = False

    publico_objetivo: Optional[List[str]] = None
    publico_objetivo_otro: Optional[str] = None
    horas_aprendizaje_autonomo_virtual: Optional[float] = None
    horas_actividades_aprendizaje: Optional[float] = None
    observaciones: Optional[str] = None
    etapa: Optional[str] = None  # El campo etapa ahora está aquí

    class Config:
        from_attributes = True


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    ultima_actualizacion: Optional[datetime] = None

