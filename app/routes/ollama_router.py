from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import requests

router = APIRouter(
    prefix="/ollama",
    tags=["Ollama - IA Local"]
)

OLLAMA_MCP_URL = "http://localhost:8002"

class GenerateRequest(BaseModel):
    entity_type: str
    context: Dict[str, Any]
    action: str = "generate"

class AnalyzeRequest(BaseModel):
    content: str
    analysis_type: str
    context: Optional[Dict[str, Any]] = None

class ImproveRequest(BaseModel):
    content: str
    entity_type: str
    improvement_type: str = "general"

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "llama3.2"
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None
    temperature: float = 0.7
    max_tokens: int = 2048

SYSTEM_PROMPT = """Eres un asistente especializado en educación y diseño instruccional 
para una plataforma de gestión de cursos virtuales. Ayudas a usuarios a crear contenido 
educativo de calidad, diseñar actividades de aprendizaje y mejorar materiales existentes."""

def call_ollama(prompt: str, system: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """Llama al MCP de Ollama"""
    payload = {
        "prompt": prompt,
        "model": "llama3.2",
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    if system:
        payload["system"] = system
    
    response = requests.post(f"{OLLAMA_MCP_URL}/generate", json=payload, timeout=120)
    response.raise_for_status()
    return response.json().get("response", "")

@router.get("/")
def root():
    return {"message": "Ollama MCP API", "status": "running"}

@router.get("/health")
def health():
    try:
        response = requests.get(f"{OLLAMA_MCP_URL}/health", timeout=10)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/models")
def list_models():
    try:
        response = requests.get(f"{OLLAMA_MCP_URL}/models", timeout=10)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/{entity_type}")
def generate_content(entity_type: str, action: str = "generate", context: Optional[Dict[str, Any]] = None):
    """Genera contenido para cualquier entidad del sistema."""
    try:
        result = call_ollama(
            prompt=f"Contexto: {context}\nAcción: {action}\nTipo de entidad: {entity_type}\n\nGenera el contenido solicitado:",
            system=SYSTEM_PROMPT
        )
        return {"response": result, "entity_type": entity_type, "action": action}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
def generate_content_body(req: GenerateRequest):
    """Genera contenido usando el body completo."""
    try:
        result = call_ollama(
            prompt=f"Contexto: {req.context}\nAcción: {req.action}\nTipo de entidad: {req.entity_type}",
            system=SYSTEM_PROMPT
        )
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
def analyze_content(req: AnalyzeRequest):
    """Analiza contenido educativo."""
    try:
        prompt = f"Analiza el siguiente contenido:\n\n{req.content}\n\nTipo de análisis: {req.analysis_type}"
        if req.context:
            prompt += f"\n\nContexto adicional: {req.context}"
        result = call_ollama(prompt, system=SYSTEM_PROMPT)
        return {"analysis": result, "type": req.analysis_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/{analysis_type}")
def analyze_content_type(analysis_type: str, content: str, context: Optional[Dict[str, Any]] = None):
    """Analiza contenido especificando el tipo en la URL."""
    try:
        prompt = f"Analiza el siguiente contenido:\n\n{content}\n\nTipo de análisis: {analysis_type}"
        if context:
            prompt += f"\n\nContexto adicional: {context}"
        result = call_ollama(prompt, system=SYSTEM_PROMPT)
        return {"analysis": result, "type": analysis_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/improve")
def improve_content(req: ImproveRequest):
    """Mejora contenido existente."""
    try:
        prompt = f"Mejora el siguiente contenido usando el tipo de mejora '{req.improvement_type}':\n\n{req.content}"
        result = call_ollama(prompt, system=SYSTEM_PROMPT)
        return {"improved_content": result, "type": req.improvement_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/improve/{entity_type}/{improvement_type}")
def improve_content_type(entity_type: str, improvement_type: str, content: str):
    """Mejora contenido especificando tipo y mejora en URL."""
    try:
        prompt = f"Mejora el siguiente contenido ({entity_type}) usando '{improvement_type}':\n\n{content}"
        result = call_ollama(prompt, system=SYSTEM_PROMPT)
        return {"improved_content": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
def chat(req: ChatRequest):
    """Chat interactivo con contexto del proyecto."""
    messages = []
    if req.history:
        for msg in req.history:
            messages.append(msg)
    
    user_message = req.message
    if req.context:
        user_message += f"\n\nContexto adicional: {req.context}"
    
    messages.append(user_message)
    
    try:
        full_prompt = f"Historial de conversación:\n{messages}\n\nUsuario: {req.message}\nAsistente:"
        response = call_ollama(
            prompt=full_prompt,
            system=SYSTEM_PROMPT,
            temperature=req.temperature,
            max_tokens=req.max_tokens
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/project/description")
def generate_project_description(name: str, tipo_proyecto: Optional[str] = None, 
                                 idioma: str = "Español", horas: Optional[float] = None):
    """Genera descripción para un proyecto."""
    prompt = f"Genera una descripción profesional para un proyecto llamado '{name}'"
    if tipo_proyecto:
        prompt += f" de tipo '{tipo_proyecto}'"
    if horas:
        prompt += f" con duración de {horas} horas"
    prompt += f" en idioma {idioma}."
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/project/target-audience")
def generate_project_target(name: str, tipo_proyecto: Optional[str] = None, 
                            horas: Optional[float] = None):
    """Sugiere público objetivo para un proyecto."""
    prompt = f"Sugiere el público objetivo para un proyecto llamado '{name}'"
    if tipo_proyecto:
        prompt += f" de tipo '{tipo_proyecto}'"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/study-plan/objective")
def generate_study_plan_objective(name: str, modalidad: Optional[str] = None, 
                                   duracion: Optional[int] = None):
    """Genera objetivo general para un plan de estudio."""
    prompt = f"Genera el objetivo general para un plan de estudio llamado '{name}'"
    if modalidad:
        prompt += f" en modalidad {modalidad}"
    if duracion:
        prompt += f" con duración de {duracion} horas"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/study-plan/objectives")
def generate_study_plan_specific_objectives(objetivo_general: str):
    """Genera objetivos específicos desde el objetivo general."""
    prompt = f"A partir del siguiente objetivo general, genera objetivos específicos:\n\n{objetivo_general}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/course/description")
def generate_course_description(name: str, module_name: Optional[str] = None, 
                                horas: Optional[int] = None):
    """Genera descripción para un curso."""
    prompt = f"Genera una descripción para un curso llamado '{name}'"
    if module_name:
        prompt += f" del módulo '{module_name}'"
    if horas:
        prompt += f" de {horas} horas"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/course/syllabus")
def generate_course_syllabus(name: str, description: str, horas: int):
    """Genera temario para un curso."""
    prompt = f"Genera un temario detallado para un curso llamado '{name}' con la siguiente descripción:\n\n{description}\n\nDuración: {horas} horas"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/module/keywords")
def generate_module_keywords(name: str, course_name: str):
    """Genera palabras clave para un módulo."""
    prompt = f"Genera palabras clave para un módulo llamado '{name}' del curso '{course_name}'"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/module/structure")
def generate_module_structure(name: str, course_name: str, horas: int):
    """Sugiere estructura de unidades para un módulo."""
    prompt = f"Sugiere la estructura de unidades para un módulo llamado '{name}' del curso '{course_name}' con {horas} horas de duración"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/unit/content")
def generate_unit_content(name: str, module_name: str, objectives: str):
    """Genera contenido para una unidad."""
    prompt = f"Genera contenido educativo para una unidad llamada '{name}' del módulo '{module_name}' con los siguientes objetivos:\n\n{objectives}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/unit/glossary")
def generate_unit_glossary(name: str, content: str):
    """Genera glosario para una unidad."""
    prompt = f"Genera un glosario de términos para la unidad '{name}' basándote en el siguiente contenido:\n\n{content}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/task/subtasks")
def generate_task_subtasks(titulo: str, descripcion: str, 
                           fecha_entrega: Optional[str] = None):
    """Sugiere subtareas para una tarea."""
    prompt = f"Sugiere subtareas para la siguiente tarea:\n\nTítulo: {titulo}\nDescripción: {descripcion}"
    if fecha_entrega:
        prompt += f"\nFecha de entrega: {fecha_entrega}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/task/time-estimate")
def estimate_task_time(titulo: str, descripcion: str, complejidad: str = "media"):
    """Estima tiempo para una tarea."""
    prompt = f"Estima el tiempo necesario para completar la siguiente tarea (complejidad: {complejidad}):\n\nTítulo: {titulo}\nDescripción: {descripcion}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/instructional-design/objective")
def generate_id_objective(course_name: str, module_name: Optional[str] = None, 
                          mensaje_clave: Optional[str] = None):
    """Genera objetivo instruccional."""
    prompt = f"Genera un objetivo instruccional para el curso '{course_name}'"
    if module_name:
        prompt += f" del módulo '{module_name}'"
    if mensaje_clave:
        prompt += f" con el mensaje clave: {mensaje_clave}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/instructional-design/activities")
def generate_id_activities(objetivo: str, publica: str, duracion: Optional[str] = None):
    """Sugiere actividades de aprendizaje."""
    prompt = f"Sugiere actividades de aprendizaje para el siguiente objetivo:\n\n{objetivo}\n\nPúblico: {publica}"
    if duracion:
        prompt += f"\nDuración: {duracion}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/instructional-design/validate")
def validate_instructional_design(form_data: Dict[str, Any]):
    """Valida coherencia del diseño instruccional."""
    prompt = f"Valida la coherencia del siguiente diseño instruccional:\n\n{form_data}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/author/structure")
def generate_author_structure(course_name: str, module_name: Optional[str] = None, 
                              horas: Optional[int] = None):
    """Sugiere estructura para contenido de autor."""
    prompt = f"Sugiere una estructura de contenido para el curso '{course_name}'"
    if module_name:
        prompt += f" módulo '{module_name}'"
    if horas:
        prompt += f" de {horas} horas"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/author/glossary")
def generate_author_glossary(contenido: str):
    """Genera glosario desde contenido."""
    prompt = f"Genera un glosario de términos técnicos del siguiente contenido:\n\n{contenido}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/author/improve")
def improve_author_content(contenido: str):
    """Mejora contenido de autor."""
    prompt = f"Mejora el siguiente contenido educativo:\n\n{contenido}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}

@router.post("/generate/learning-activity/suggest")
def suggest_learning_activity(unit_name: str, objective: str):
    """Sugiere tipo de actividad de aprendizaje."""
    prompt = f"Sugiere un tipo de actividad de aprendizaje apropiada para la unidad '{unit_name}' con el objetivo: {objective}"
    return {"response": call_ollama(prompt, SYSTEM_PROMPT)}
