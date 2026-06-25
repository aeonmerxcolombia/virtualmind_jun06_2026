# app/routes/ai_router.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.services.ai.mcp_service import mcp_service

router = APIRouter(
    prefix="/ai",
    tags=["Inteligencia Artificial - MCP"]
)

# ========================
# MODELOS DE PETICIÓN
# ========================

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
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None

# ========================
# ENDPOINTS GENERATIVOS
# ========================

@router.post("/generate/{entity_type}")
def generate_content(
    entity_type: str,
    action: str = "generate",
    context: Optional[Dict[str, Any]] = None
):
    """
    Genera contenido para cualquier entidad del sistema.
    
    entity_type: project, study_plan, course, module, unit, task, 
                 instructional_design, author_content, learning_activity
    action: description, suggest_target, structure, objective, etc.
    """
    try:
        result = mcp_service.generate_content(
            entity_type=entity_type,
            context=context or {},
            action=action
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
def generate_content_body(req: GenerateRequest):
    """Genera contenido usando el body completo."""
    try:
        result = mcp_service.generate_content(
            entity_type=req.entity_type,
            context=req.context,
            action=req.action
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# ENDPOINTS DE ANÁLISIS
# ========================

@router.post("/analyze")
def analyze_content(req: AnalyzeRequest):
    """
    Analiza contenido educativo.
    
    analysis_type: coherence, quality, accessibility, learning_objectives
    """
    try:
        result = mcp_service.analyze(
            content=req.content,
            analysis_type=req.analysis_type,
            context=req.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/{analysis_type}")
def analyze_content_type(
    analysis_type: str,
    content: str,
    context: Optional[Dict[str, Any]] = None
):
    """Analiza contenido especificando el tipo en la URL."""
    try:
        result = mcp_service.analyze(
            content=content,
            analysis_type=analysis_type,
            context=context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# ENDPOINTS DE MEJORA
# ========================

@router.post("/improve")
def improve_content(req: ImproveRequest):
    """
    Mejora contenido existente.
    
    improvement_type: grammar, clarity, pedagogical, engagement, general
    """
    try:
        result = mcp_service.improve_content(
            content=req.content,
            entity_type=req.entity_type,
            improvement_type=req.improvement_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/improve/{entity_type}/{improvement_type}")
def improve_content_type(
    entity_type: str,
    improvement_type: str,
    content: str
):
    """Mejora contenido especificando tipo y mejora en URL."""
    try:
        result = mcp_service.improve_content(
            content=content,
            entity_type=entity_type,
            improvement_type=improvement_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# CHAT INTERACTIVO
# ========================

@router.post("/chat")
def chat(req: ChatRequest):
    """Chat interactivo con contexto del proyecto."""
    system_prompt = """Eres un asistente especializado en educación y diseño instruccional 
    para una plataforma de gestión de cursos virtuales. Ayudas a usuarios a crear contenido 
    educativo de calidad, diseñar actividades de aprendizaje y mejorar materiales existentes."""
    
    # Construir historial
    messages = []
    if req.history:
        for msg in req.history:
            messages.append(msg)
    
    # Agregar mensaje actual
    user_message = req.message
    if req.context:
        user_message += f"\n\nContexto adicional: {req.context}"
    
    messages.append(user_message)
    
    try:
        response = mcp_service.generate(
            prompt=user_message,
            system_instruction=system_prompt,
            temperature=0.7
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# ENDPOINTS ESPECÍFICOS
# ========================

@router.post("/generate/project/description")
def generate_project_description(name: str, tipo_proyecto: Optional[str] = None, 
                                 idioma: str = "Español", horas: Optional[float] = None):
    """Genera descripción para un proyecto."""
    context = {"name": name, "tipo_proyecto": tipo_proyecto, "idioma": idioma, "horas_curso": horas}
    return mcp_service.generate_content("project", context, "description")

@router.post("/generate/project/target-audience")
def generate_project_target(name: str, tipo_proyecto: Optional[str] = None, 
                            horas: Optional[float] = None):
    """Sugiere público objetivo para un proyecto."""
    context = {"name": name, "tipo_proyecto": tipo_proyecto, "horas_curso": horas}
    return mcp_service.generate_content("project", context, "suggest_target")

@router.post("/generate/study-plan/objective")
def generate_study_plan_objective(name: str, modalidad: Optional[str] = None, 
                                   duracion: Optional[int] = None):
    """Genera objetivo general para un plan de estudio."""
    context = {"name": name, "modalidad": modalidad, "duracion": duracion}
    return mcp_service.generate_content("study_plan", context, "general_objective")

@router.post("/generate/study-plan/objectives")
def generate_study_plan_specific_objectives(objetivo_general: str):
    """Genera objetivos específicos desde el objetivo general."""
    context = {"objetivo_general": objetivo_general}
    return mcp_service.generate_content("study_plan", context, "specific_objectives")

@router.post("/generate/course/description")
def generate_course_description(name: str, module_name: Optional[str] = None, 
                                horas: Optional[int] = None):
    """Genera descripción para un curso."""
    context = {"name": name, "module_name": module_name, "horas": horas}
    return mcp_service.generate_content("course", context, "description")

@router.post("/generate/course/syllabus")
def generate_course_syllabus(name: str, description: str, horas: int):
    """Genera temario para un curso."""
    context = {"name": name, "description": description, "horas": horas}
    return mcp_service.generate_content("course", context, "syllabus")

@router.post("/generate/module/keywords")
def generate_module_keywords(name: str, course_name: str):
    """Genera palabras clave para un módulo."""
    context = {"name": name, "course_name": course_name}
    return mcp_service.generate_content("module", context, "keywords")

@router.post("/generate/module/structure")
def generate_module_structure(name: str, course_name: str, horas: int):
    """Sugiere estructura de unidades para un módulo."""
    context = {"name": name, "course_name": course_name, "horas": horas}
    return mcp_service.generate_content("module", context, "structure")

@router.post("/generate/unit/content")
def generate_unit_content(name: str, module_name: str, objectives: str):
    """Genera contenido para una unidad."""
    context = {"name": name, "module_name": module_name, "objectives": objectives}
    return mcp_service.generate_content("unit", context, "content")

@router.post("/generate/unit/glossary")
def generate_unit_glossary(name: str, content: str):
    """Genera glosario para una unidad."""
    context = {"name": name, "content": content}
    return mcp_service.generate_content("unit", context, "glossary")

@router.post("/generate/task/subtasks")
def generate_task_subtasks(titulo: str, descripcion: str, 
                           fecha_entrega: Optional[str] = None):
    """Sugiere subtareas para una tarea."""
    context = {"titulo": titulo, "descripcion": descripcion, "fecha_entrega": fecha_entrega}
    return mcp_service.generate_content("task", context, "subtasks")

@router.post("/generate/task/time-estimate")
def estimate_task_time(titulo: str, descripcion: str, complejidad: str = "media"):
    """Estima tiempo para una tarea."""
    context = {"titulo": titulo, "descripcion": descripcion, "complejidad": complejidad}
    return mcp_service.generate_content("task", context, "time_estimate")

@router.post("/generate/instructional-design/objective")
def generate_id_objective(course_name: str, module_name: Optional[str] = None, 
                          mensaje_clave: Optional[str] = None):
    """Genera objetivo instruccional."""
    context = {"course_name": course_name, "module_name": module_name, 
               "mensaje_clave": mensaje_clave}
    return mcp_service.generate_content("instructional_design", context, "objective")

@router.post("/generate/instructional-design/activities")
def generate_id_activities(objetivo: str, publica: str, duracion: Optional[str] = None):
    """Sugiere actividades de aprendizaje."""
    context = {"objetivo": objetivo, "publico": publica, "duracion": duracion}
    return mcp_service.generate_content("instructional_design", context, "activities")

@router.post("/generate/instructional-design/validate")
def validate_instructional_design(form_data: Dict[str, Any]):
    """Valida coherencia del diseño instruccional."""
    return mcp_service.generate_content("instructional_design", form_data, "validate")

@router.post("/generate/author/structure")
def generate_author_structure(course_name: str, module_name: Optional[str] = None, 
                              horas: Optional[int] = None):
    """Sugiere estructura para contenido de autor."""
    context = {"course_name": course_name, "module_name": module_name, "horas_curso": horas}
    return mcp_service.generate_content("author_content", context, "structure")

@router.post("/generate/author/glossary")
def generate_author_glossary(contenido: str):
    """Genera glosario desde contenido."""
    context = {"contenido": contenido}
    return mcp_service.generate_content("author_content", context, "glossary")

@router.post("/generate/author/improve")
def improve_author_content(contenido: str):
    """Mejora contenido de autor."""
    context = {"contenido": contenido}
    return mcp_service.generate_content("author_content", context, "improve")

@router.post("/generate/learning-activity/suggest")
def suggest_learning_activity(unit_name: str, objective: str):
    """Sugiere tipo de actividad de aprendizaje."""
    context = {"unit_name": unit_name, "objective": objective}
    return mcp_service.generate_content("learning_activity", context, "suggest")

# ========================
# HEALTH CHECK
# ========================

@router.get("/health")
def ai_health():
    """Verifica que el servicio de IA esté disponible."""
    return {
        "status": "ok",
        "model": "gemini-2.0-flash",
        "available_entities": [
            "project", "study_plan", "course", "module", "unit", 
            "task", "instructional_design", "author_content", "learning_activity"
        ]
    }
