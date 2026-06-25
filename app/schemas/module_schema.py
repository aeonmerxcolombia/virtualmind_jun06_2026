# app/schemas/module_schema.py

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict, Union
from datetime import datetime

class ModuleBase(BaseModel):
    # K. Fechas y control (campos de formulario, no los generados por DB)
    notas_adicionales: Optional[str] = None
    
    # A. Identificación
    nombre_del_modulo: Optional[str] = None
    nombre_corto_del_modulo: Optional[str] = None
    codigo_id_del_modulo: Optional[str] = None
    version: Optional[str] = None
    palabras_clave: Optional[Union[str, List]] = None
    autor_responsable: Optional[str] = None
    derechos_patrimoniales: Optional[bool] = None
    derechos_intelectuales: Optional[bool] = None
    organizacion_institucion: Optional[str] = None

    # B. Objetivos y alcance
    objetivo_general: Optional[str] = None
    objetivos_especificos: Optional[str] = None
    publico_objetivo: Optional[str] = None
    duracion_estimada: Optional[str] = None
    requisitos_previos: Optional[str] = None
    criterios_de_logro: Optional[str] = None

    # C. Estructura de contenidos
    numero_unidades: Optional[int] = None
    lista_unidades_temas: Optional[str] = None
    orden_unidades: Optional[str] = None
    tiempo_estimado_por_unidad: Optional[str] = None

    # D. Diseño visual y marca
    tipo_letra: Optional[str] = None
    tamano_letra: Optional[str] = None
    estilos_texto: Optional[str] = None
    colores_principales: Optional[str] = None
    logotipo: Optional[str] = None

    # E. Portada
    tiene_portada: Optional[bool] = None
    tipo_portada: Optional[str] = None
    creditos_en_portada: Optional[bool] = None
    texto_de_portada: Optional[str] = None

    # F. Recursos multimedia
    infografias_estaticas: Optional[int] = None
    infografias_animadas: Optional[int] = None
    imagenes: Optional[int] = None
    videos: Optional[str] = None
    microvideos_cortos: Optional[bool] = None
    audios: Optional[str] = None
    animaciones: Optional[int] = None
    storytelling: Optional[bool] = None
    presentaciones_interactivas: Optional[bool] = None
    portada_animada: Optional[bool] = None
    gamificacion: Optional[bool] = None
    simulaciones: Optional[bool] = None
    realidad_aumentada: Optional[bool] = None
    lineas_tiempo_interactivas: Optional[bool] = None
    mapas_interactivos: Optional[bool] = None
    galerias_imagenes: Optional[bool] = None
    elementos_descargables: Optional[str] = None
    otros_recursos: Optional[str] = None
    
    # G. Actividades e interactividad
    actividades_aprendizaje_unidad: Optional[str] = None
    actividades_cierre_modulo: Optional[str] = None
    tipos_actividades: Optional[str] = None
    materiales_descargables: Optional[str] = None
    
    # H. Evaluación
    tipos_preguntas: Optional[str] = None
    numero_total_preguntas: Optional[int] = None
    nota_minima_aprobacion: Optional[float] = None
    intentos_permitidos: Optional[int] = None
    tiempo_limite: Optional[str] = None
    retroalimentacion: Optional[str] = None

    # I. Accesibilidad e inclusión
    subtitulos_videos: Optional[bool] = None
    transcripciones_audio: Optional[bool] = None
    navegacion_teclado: Optional[bool] = None
    lectura_pantalla_compatible: Optional[bool] = None
    idiomas_disponibles: Optional[str] = None

    # J. Entrega y uso
    plataforma_destino: Optional[str] = None
    dispositivos_objetivo: Optional[str] = None
    modo_uso: Optional[str] = None
    tamano_aproximado: Optional[str] = None
    entrega_fuentes: Optional[bool] = None
    entrega_scorm: Optional[bool] = None
    entrega_multimedia: Optional[bool] = None
    entrega_version_pdf: Optional[bool] = None

class ModuleCreate(ModuleBase):
    study_plan_id: int

class ModuleUpdate(ModuleBase):
    study_plan_id: Optional[int] = None

class ModuleOut(ModuleBase):
    id: int
    study_plan_id: int
    fecha_creacion: datetime
    ultima_actualizacion: datetime

    class Config:
        from_attributes = True
