from typing import Any, Dict, List
from sqlalchemy import text
from mcp_server.db import SessionLocal
from mcp_server.tools.ai import generate_json_with_ai

def get_all_courses(limit: int = 50) -> List[Dict[str, Any]]:
    """Obtiene todos los cursos."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, name, description, author, created_at, updated_at
            FROM courses 
            ORDER BY id DESC 
            LIMIT :limit
        """), {"limit": limit})
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_course_by_id(course_id: int) -> Dict[str, Any]:
    """Obtiene un curso por ID con sus módulos y unidades."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT * FROM courses WHERE id = :id
        """), {"id": course_id})
        
        row = result.fetchone()
        if not row:
            return {"error": "Curso no encontrado"}
        
        course = dict(row._mapping)
        
        modules = db.execute(text("""
            SELECT * FROM modules WHERE course_id = :course_id
        """), {"course_id": course_id})
        course["modules"] = [dict(m._mapping) for m in modules]
        
        for module in course["modules"]:
            units = db.execute(text("""
                SELECT * FROM units WHERE module_id = :module_id
            """), {"module_id": module["id"]})
            module["units"] = [dict(u._mapping) for u in units]
        
        return course
    finally:
        db.close()

def get_courses_by_project(project_id: int) -> List[Dict[str, Any]]:
    """Obtiene cursos de un proyecto."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT c.id, c.name, c.author
            FROM courses c
            WHERE c.study_plan_id = :project_id
            ORDER BY c.id DESC
        """), {"project_id": project_id})
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def generate_course_structure(
    course_name: str,
    horas: int,
    idioma: str = "Español",
    public: str = "General"
) -> Dict[str, Any]:
    """Genera estructura de un curso con IA."""
    prompt = f"""Genera una estructura completa para un curso educativo:

Nombre: {course_name}
Horas: {horas}
Idioma: {idioma}
Público: {public}

Responde en JSON:
{{
    "descripcion": "Descripción del curso",
    "modulos": [
        {{
            "nombre": "Módulo 1: Introducción",
            "descripcion": "...",
            "horas": 4,
            "unidades": [
                {{"nombre": "Unidad 1.1", "temas": ["tema1"], "horas": 2}}
            ]
        }}
    ],
    "objetivos_generales": ["obj1"],
    "resultados_aprendizaje": ["resultado1"],
    "recursos_necesarios": ["recurso1"],
    "estrategias_didacticas": ["estrategia1"]
}}"""
    
    return generate_json_with_ai(
        prompt=prompt,
        system_instruction="Eres un experto en diseño instruccional y creación de cursos."
    )

def analyze_course_quality(course_id: int) -> Dict[str, Any]:
    """Analiza la calidad de un curso con IA."""
    course = get_course_by_id(course_id)
    
    if "error" in course:
        return course
    
    prompt = f"""Analiza la calidad del siguiente curso:

Título: {course.get('name')}
Descripción: {course.get('description')}
Autor: {course.get('author')}
Módulos: {len(course.get('modules', []))}

Responde en JSON:
{{
    "calidad_general": "alta/media/baja",
    "fortalezas": ["fortaleza1"],
    "debilidades": ["debilidad1"],
    "sugerencias_mejora": ["sugerencia1"],
    "coherencia_estructural": "alta/media/baja",
    "recomendaciones": ["rec1"]
}}"""
    
    return generate_json_with_ai(
        prompt=prompt,
        system_instruction="Eres un experto en evaluación de calidad de cursos educativos."
    )
