# app/schemas/unit_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List
from .learning_activity_schema import LearningActivityOut  # Importa el esquema de actividades

# Esquema base que define los campos comunes
class UnitBase(BaseModel):
    # Información básica y heredada
    name: str = Field(..., example="Unidad 1. Fundamentos de Algoritmos", description="Nombre de la unidad")
    short_name: str = Field(..., example="Fundamentos de Algoritmos", description="Nombre corto de la Unidad")
    unit_code: Optional[str] = Field(None, example="UA1", description="Código / ID de la unidad (Heredado del modulo)")
    
    # Objetivos
    general_objective: str = Field(..., example="Introducir los conceptos básicos de algoritmos y su importancia.", description="Objetivo general de la unidad")
    specific_objectives: Optional[str] = Field(None, example="1. Definir qué es un algoritmo. 2. Identificar tipos de algoritmos. 3. Crear algoritmos secuenciales simples.", description="Objetivos específicos de la unidad (Heredan del Modulo segun escrito de autoria)")
    
    # Contenido y duración
    duration: Optional[str] = Field(None, example="2 horas", description="Duración estimada (min/horas) (Esta dentro del rango de tiempo del modulo...)")
    contents: Optional[str] = Field(None, example="1. Definición de algoritmo. 2. Características. 3. Tipos. 4. Representación. 5. Estructuras secuenciales.", description="Contenidos / sub temas incluidos (Estan en el escrito de contenidos)")
    
    # Recursos
    multimedia_resources: Optional[str] = Field(None, example="Video explicativo, Infografía, Simulador de algoritmos", description="Recursos multimedia (Los mismos del modulo, colocar cada tipo de formato)")
    
    # Actividades
    has_activities: bool = Field(default=True, description="Indica presencia de actividades (minimo una por unidad)")
    activity_types: Optional[str] = Field(None, example="Cuestionario, Foro de discusión", description="Tipo de actividades (Las mismas del modulo)")
    activity_instructions: Optional[str] = Field(None, example="Realizar el cuestionario sobre conceptos básicos. Participar en el foro de definiciones.", description="Instrucciones de actividades (Las mismas del modulo)")
    
    # Evaluación y otros
    has_downloadable_materials: bool = Field(default=False, description="Materiales descargables (Si o no)")
    has_assessment: bool = Field(default=False, description="Evaluación asociada a la unidad (Si o no)")
    accessibility: Optional[str] = Field(None, example="Compatible con lectores de pantalla, Contraste ajustable", description="Accesibilidad")
    additional_notes: Optional[str] = Field(None, example="Material adicional disponible en el repositorio del curso.", description="Notas adicionales")
    
    # Relación con el módulo
    module_id: int = Field(..., example=1, description="ID del módulo al que pertenece esta unidad")

# Esquema para crear una nueva unidad
class UnitCreate(UnitBase):
    pass

# Esquema para actualizar una unidad (todos los campos son opcionales)
class UnitUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    unit_code: Optional[str] = None
    general_objective: Optional[str] = None
    specific_objectives: Optional[str] = None
    duration: Optional[str] = None
    contents: Optional[str] = None
    multimedia_resources: Optional[str] = None
    has_activities: Optional[bool] = None
    activity_types: Optional[str] = None
    activity_instructions: Optional[str] = None
    has_downloadable_materials: Optional[bool] = None
    has_assessment: Optional[bool] = None
    accessibility: Optional[str] = None
    additional_notes: Optional[str] = None
    module_id: Optional[int] = None

# Esquema para leer/retornar datos de una unidad, incluyendo su ID y actividades relacionadas
class UnitRead(UnitBase):
    id: int
    learning_activities: List[LearningActivityOut] = []  # Relación con las actividades

    class Config:
        # Permite que Pydantic cree instancias desde objetos ORM (como los de SQLAlchemy)
        from_attributes = True # Compatible con Pydantic v2. Para v1 era orm_mode = True

