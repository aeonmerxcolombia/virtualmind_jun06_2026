from typing import Any, Dict, List
from sqlalchemy import text
from mcp_server.db import SessionLocal
from mcp_server.tools.ai import generate_json_with_ai

def get_dashboard_stats() -> Dict[str, Any]:
    """Obtiene estadísticas generales del dashboard."""
    db = SessionLocal()
    try:
        total_projects = db.execute(text("SELECT COUNT(*) as count FROM projects")).fetchone()
        active_projects = db.execute(text("SELECT COUNT(*) as count FROM projects WHERE estado = 'En Desarrollo'")).fetchone()
        completed_projects = db.execute(text("SELECT COUNT(*) as count FROM projects WHERE estado = 'Completado'")).fetchone()
        
        total_users = db.execute(text("SELECT COUNT(*) as count FROM usuarios")).fetchone()
        active_users = db.execute(text("SELECT COUNT(*) as count FROM usuarios WHERE estado = 'activo'")).fetchone()
        
        total_courses = db.execute(text("SELECT COUNT(*) as count FROM courses")).fetchone()
        
        pending_tasks = db.execute(text("SELECT COUNT(*) as count FROM tareas WHERE estado != 'completada'")).fetchone()
        
        return {
            "proyectos": {
                "total": total_projects[0] if total_projects else 0,
                "activos": active_projects[0] if active_projects else 0,
                "completados": completed_projects[0] if completed_projects else 0
            },
            "usuarios": {
                "total": total_users[0] if total_users else 0,
                "activos": active_users[0] if active_users else 0
            },
            "cursos": {
                "total": total_courses[0] if total_courses else 0
            },
            "tareas": {
                "pendientes": pending_tasks[0] if pending_tasks else 0
            }
        }
    finally:
        db.close()

def get_projects_by_state() -> List[Dict[str, Any]]:
    """Obtiene proyectos agrupados por estado."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT estado, COUNT(*) as count 
            FROM projects 
            GROUP BY estado
            ORDER BY count DESC
        """))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_projects_by_type() -> List[Dict[str, Any]]:
    """Obtiene proyectos agrupados por tipo."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT tipo_proyecto, COUNT(*) as count 
            FROM projects 
            WHERE tipo_proyecto IS NOT NULL
            GROUP BY tipo_proyecto
            ORDER BY count DESC
            LIMIT 10
        """))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_projects_timeline() -> List[Dict[str, Any]]:
    """Obtiene línea de tiempo de proyectos."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, name, start_date, end_date, estado
            FROM projects 
            WHERE start_date IS NOT NULL
            ORDER BY start_date DESC
            LIMIT 20
        """))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_top_users_by_tasks() -> List[Dict[str, Any]]:
    """Obtiene usuarios con más tareas asignadas."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT asignado_a, COUNT(*) as total_tareas,
                   SUM(CASE WHEN estado = 'completada' THEN 1 ELSE 0 END) as tareas_completadas
            FROM tareas 
            WHERE asignado_a IS NOT NULL
            GROUP BY asignado_a
            ORDER BY total_tareas DESC
            LIMIT 10
        """))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def generate_dashboard_report() -> Dict[str, Any]:
    """Genera reporte de dashboard con IA."""
    stats = get_dashboard_stats()
    projects_by_state = get_projects_by_state()
    projects_by_type = get_projects_by_type()
    
    prompt = f"""Analiza las siguientes estadísticas del sistema y genera un reporte:

Proyectos: {stats.get('proyectos')}
Usuarios: {stats.get('usuarios')}
Cursos: {stats.get('cursos')}
Tareas: {stats.get('tareas')}

Proyectos por estado: {projects_by_state}
Proyectos por tipo: {projects_by_type}

Responde en JSON:
{{
    "resumen_ejecutivo": "Resumen de la situación actual",
    "alertas": ["alerta1"],
    "recomendaciones": ["rec1"],
    "tendencias": ["tendencia1"],
    "salud_sistema": "buena/regular/mala"
}}"""
    
    return generate_json_with_ai(
        prompt=prompt,
        system_instruction="Eres un experto en análisis de datos y métricas de proyectos."
    )
