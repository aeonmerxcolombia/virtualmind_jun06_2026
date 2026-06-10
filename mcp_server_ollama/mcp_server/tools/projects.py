from typing import Any, Dict, List
from sqlalchemy import text
from mcp_server.db import SessionLocal
from mcp_server.tools.ai import generate_json_with_ai, generate_with_ai

# ============ CONSULTAS (READ) ============

def get_all_projects(limit: int = 50) -> List[Dict[str, Any]]:
    """Obtiene todos los proyectos."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, name, client_id, estado, start_date, end_date, 
                   tipo_proyecto, description, idioma, etapa
            FROM projects 
            ORDER BY id DESC 
            LIMIT :limit
        """), {"limit": limit})
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_project_by_id(project_id: int) -> Dict[str, Any]:
    """Obtiene un proyecto por ID con todos sus detalles."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT * FROM projects WHERE id = :id
        """), {"id": project_id})
        
        row = result.fetchone()
        if not row:
            return {"error": "Proyecto no encontrado"}
        
        project = dict(row._mapping)
        
        tareas = db.execute(text("""
            SELECT * FROM tareas WHERE project_id = :project_id
        """), {"project_id": project_id})
        project["tareas"] = [dict(t._mapping) for t in tareas]
        
        cronograma = db.execute(text("""
            SELECT * FROM cronogramas WHERE project_id = :project_id
        """), {"project_id": project_id})
        cron = cronograma.fetchone()
        if cron:
            project["cronograma"] = dict(cron._mapping)
        
        return project
    finally:
        db.close()

def get_projects_by_client(client_id: str) -> List[Dict[str, Any]]:
    """Obtiene proyectos de un cliente."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, name, estado, start_date, end_date, tipo_proyecto
            FROM projects 
            WHERE client_id = :client_id
            ORDER BY id DESC
        """), {"client_id": client_id})
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def search_projects(query: str) -> List[Dict[str, Any]]:
    """Busca proyectos por nombre o descripción."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, name, estado, tipo_proyecto, description
            FROM projects 
            WHERE name LIKE :query OR description LIKE :query
            ORDER BY id DESC
            LIMIT 20
        """), {"query": f"%{query}%"})
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def analyze_project_with_ai(project_id: int) -> Dict[str, Any]:
    """Analiza un proyecto con IA y sugiere mejoras."""
    project = get_project_by_id(project_id)
    
    if "error" in project:
        return project
    
    prompt = f"""Analiza el siguiente proyecto educativo y proporciona suggestions de mejora:

Nombre: {project.get('name')}
Tipo: {project.get('tipo_proyecto')}
Estado: {project.get('estado')}
Descripción: {project.get('description')}
Idioma: {project.get('idioma')}
Fecha inicio: {project.get('start_date')}
Fecha fin: {project.get('end_date')}
Etapa: {project.get('etapa')}

Número de tareas: {len(project.get('tareas', []))}
Cronograma: {project.get('cronograma', {})}

Responde en JSON con:
{{
    "analisis": "Resumen del análisis",
    "fortalezas": ["fortaleza1"],
    "areas_mejora": ["mejora1"],
    "sugerencias": ["sugerencia1"],
    "recomendaciones_prioritarias": ["rec1"],
    "viabilidad": "alta/media/baja"
}}"""
    
    return generate_json_with_ai(
        prompt=prompt,
        system_instruction="Eres un experto en gestión de proyectos educativos y diseño instruccional."
    )

def generate_project_plan(project_name: str, tipo: str, horas: float, idioma: str = "Español") -> Dict[str, Any]:
    """Genera un plan completo para un nuevo proyecto."""
    prompt = f"""Genera un plan detallado para un proyecto educativo:

Nombre: {project_name}
Tipo: {tipo}
Horas estimadas: {horas}
Idioma: {idioma}

Responde en JSON con estructura completa:
{{
    "fases": [
        {{"nombre": "Fase 1", "descripcion": "...", "duracion_dias": 7}}
    ],
    "estructura_contenidos": [
        {{"modulo": "Módulo 1", "unidades": ["Unidad 1.1", "Unidad 1.2"]}}
    ],
    "cronograma_sugerido": {{
        "inicio": "fecha sugerida",
        "duracion_total_dias": 30
    }},
    "recursos_necesarios": ["recurso1"],
    "equipo_sugerido": ["rol1"]
}}"""
    
    return generate_json_with_ai(
        prompt=prompt,
        system_instruction="Eres un experto en planificación de proyectos educativos."
    )

# ============ CREAR (CREATE) ============

def create_project(
    name: str,
    client_id: str,
    tipo_proyecto: str,
    estado: str = "Planificado",
    description: str = "",
    idioma: str = "Español",
    start_date: str = None,
    end_date: str = None,
    etapa: str = "Etapa Contractual"
) -> Dict[str, Any]:
    """Crea un nuevo proyecto."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            INSERT INTO projects (name, client_id, tipo_proyecto, estado, description, idioma, start_date, end_date, etapa)
            VALUES (:name, :client_id, :tipo_proyecto, :estado, :description, :idioma, :start_date, :end_date, :etapa)
        """), {
            "name": name,
            "client_id": client_id,
            "tipo_proyecto": tipo_proyecto,
            "estado": estado,
            "description": description,
            "idioma": idioma,
            "start_date": start_date,
            "end_date": end_date,
            "etapa": etapa
        })
        db.commit()
        project_id = result.lastrowid
        return {"success": True, "project_id": project_id, "message": f"Proyecto '{name}' creado correctamente"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ ACTUALIZAR (UPDATE) ============

def update_project(
    project_id: int,
    name: str = None,
    estado: str = None,
    description: str = None,
    start_date: str = None,
    end_date: str = None,
    etapa: str = None
) -> Dict[str, Any]:
    """Actualiza un proyecto existente."""
    db = SessionLocal()
    try:
        # Obtener proyecto actual
        current = db.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not current:
            return {"error": "Proyecto no encontrado"}
        
        # Construir update dinámicamente
        updates = []
        params = {"id": project_id}
        
        if name is not None:
            updates.append("name = :name")
            params["name"] = name
        if estado is not None:
            updates.append("estado = :estado")
            params["estado"] = estado
        if description is not None:
            updates.append("description = :description")
            params["description"] = description
        if start_date is not None:
            updates.append("start_date = :start_date")
            params["start_date"] = start_date
        if end_date is not None:
            updates.append("end_date = :end_date")
            params["end_date"] = end_date
        if etapa is not None:
            updates.append("etapa = :etapa")
            params["etapa"] = etapa
        
        if not updates:
            return {"error": "No hay campos para actualizar"}
        
        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = :id"
        db.execute(text(query), params)
        db.commit()
        
        return {"success": True, "message": f"Proyecto {project_id} actualizado"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ ELIMINAR (DELETE) ============

def delete_project(project_id: int) -> Dict[str, Any]:
    """Elimina un proyecto."""
    db = SessionLocal()
    try:
        # Verificar que existe
        current = db.execute(text("SELECT name FROM projects WHERE id = :id"), {"id": project_id}).fetchone()
        if not current:
            return {"error": "Proyecto no encontrado"}
        
        db.execute(text("DELETE FROM projects WHERE id = :id"), {"id": project_id})
        db.commit()
        
        return {"success": True, "message": f"Proyecto '{current.name}' eliminado"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ OTRAS FUNCIONES ============

def get_projects_by_state(estado: str) -> List[Dict[str, Any]]:
    """Obtiene proyectos por estado."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, name, client_id, estado, tipo_proyecto, etapa
            FROM projects 
            WHERE estado = :estado
            ORDER BY id DESC
        """), {"estado": estado})
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_projects_timeline() -> List[Dict[str, Any]]:
    """Obtiene línea de tiempo de proyectos."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, name, start_date, end_date, estado, etapa
            FROM projects 
            WHERE start_date IS NOT NULL
            ORDER BY start_date DESC
            LIMIT 20
        """))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()
