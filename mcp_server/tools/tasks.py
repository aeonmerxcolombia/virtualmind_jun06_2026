from typing import Any, Dict, List
from sqlalchemy import text
from mcp_server.db import SessionLocal
from mcp_server.tools.ai import generate_json_with_ai

def get_tasks_by_project(project_id: int) -> List[Dict[str, Any]]:
    """Obtiene todas las tareas de un proyecto."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT * FROM tareas 
            WHERE project_id = :project_id
            ORDER BY fecha_entrega ASC
        """), {"project_id": project_id})
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_task_by_id(task_id: int) -> Dict[str, Any]:
    """Obtiene una tarea por ID."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT * FROM tareas WHERE id = :id
        """), {"id": task_id})
        
        row = result.fetchone()
        if not row:
            return {"error": "Tarea no encontrada"}
        
        return dict(row._mapping)
    finally:
        db.close()

def get_tasks_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Obtiene tareas asignadas a un usuario."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT t.*, p.name as project_name
            FROM tareas t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.asignado_a = :user_id
            ORDER BY t.fecha_entrega ASC
        """), {"user_id": user_id})
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_pending_tasks() -> List[Dict[str, Any]]:
    """Obtiene tareas pendientes."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT t.*, p.name as project_name
            FROM tareas t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.estado != 'completada'
            ORDER BY t.fecha_entrega ASC
            LIMIT 50
        """))
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def generate_task_suggestions(
    titulo: str,
    descripcion: str,
    complejidad: str = "media"
) -> Dict[str, Any]:
    """Genera sugerencias de subtareas con IA."""
    prompt = f"""Genera subtareas y sugerencias para:

Título: {titulo}
Descripción: {descripcion}
Complejidad: {complejidad}

Responde en JSON:
{{
    "subtareas": [
        {{"titulo": "Subtarea 1", "descripcion": "...", "duracion_estimada": "1 hora"}}
    ],
    "tiempo_estimado_total": "4 horas",
    "desglose": {{"analisis": 1, "desarrollo": 2, "revision": 1}},
    "recursos_necesarios": ["recurso1"],
    "consejos": ["consejo1"]
}}"""
    
    return generate_json_with_ai(
        prompt=prompt,
        system_instruction="Eres un experto en gestión de proyectos y tareas."
    )

def analyze_task_urgency(task_id: int) -> Dict[str, Any]:
    """Analiza la urgencia de una tarea con IA."""
    task = get_task_by_id(task_id)
    
    if "error" in task:
        return task
    
    prompt = f"""Analiza la urgencia de la siguiente tarea:

Título: {task.get('titulo')}
Descripción: {task.get('descripcion')}
Estado: {task.get('estado')}
Fecha de entrega: {task.get('fecha_entrega')}
Prioridad: {task.get('prioridad')}

Responde en JSON:
{{
    "nivel_urgencia": "alta/media/baja",
    "factores": ["factor1"],
    "recomendaciones": ["rec1"],
    "dias_hasta_entrega": 0,
    "alertas": ["alerta1"]
}}"""
    
    return generate_json_with_ai(
        prompt=prompt,
        system_instruction="Eres un experto en gestión de tareas y priorización."
    )

# ============ CREAR (CREATE) ============

def create_task(
    titulo: str,
    project_id: int,
    descripcion: str = "",
    asignado_a: str = None,
    prioridad: str = "media",
    estado: str = "pendiente",
    fecha_entrega: str = None
) -> Dict[str, Any]:
    """Crea una nueva tarea."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            INSERT INTO tareas (titulo, descripcion, project_id, asignado_a, prioridad, estado, fecha_entrega)
            VALUES (:titulo, :descripcion, :project_id, :asignado_a, :prioridad, :estado, :fecha_entrega)
        """), {
            "titulo": titulo,
            "descripcion": descripcion,
            "project_id": project_id,
            "asignado_a": asignado_a,
            "prioridad": prioridad,
            "estado": estado,
            "fecha_entrega": fecha_entrega
        })
        
        db.commit()
        task_id = result.lastrowid
        return {"success": True, "task_id": task_id, "message": f"Tarea '{titulo}' creada"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ ACTUALIZAR (UPDATE) ============

def update_task(
    task_id: int,
    titulo: str = None,
    descripcion: str = None,
    prioridad: str = None,
    estado: str = None,
    fecha_entrega: str = None,
    asignado_a: str = None
) -> Dict[str, Any]:
    """Actualiza una tarea."""
    db = SessionLocal()
    try:
        updates = []
        params = {"id": task_id}
        
        if titulo is not None:
            updates.append("titulo = :titulo")
            params["titulo"] = titulo
        if descripcion is not None:
            updates.append("descripcion = :descripcion")
            params["descripcion"] = descripcion
        if prioridad is not None:
            updates.append("prioridad = :prioridad")
            params["prioridad"] = prioridad
        if estado is not None:
            updates.append("estado = :estado")
            params["estado"] = estado
        if fecha_entrega is not None:
            updates.append("fecha_entrega = :fecha_entrega")
            params["fecha_entrega"] = fecha_entrega
        if asignado_a is not None:
            updates.append("asignado_a = :asignado_a")
            params["asignado_a"] = asignado_a
        
        if not updates:
            return {"error": "No hay campos para actualizar"}
        
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = :id"
        db.execute(text(query), params)
        db.commit()
        
        return {"success": True, "message": f"Tarea {task_id} actualizada"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

def complete_task(task_id: int) -> Dict[str, Any]:
    """Marca una tarea como completada."""
    return update_task(task_id, estado="completada")

# ============ ELIMINAR (DELETE) ============

def delete_task(task_id: int) -> Dict[str, Any]:
    """Elimina una tarea."""
    db = SessionLocal()
    try:
        current = db.execute(text("SELECT titulo FROM tareas WHERE id = :id"), {"id": task_id}).fetchone()
        if not current:
            return {"error": "Tarea no encontrada"}
        
        db.execute(text("DELETE FROM tareas WHERE id = :id"), {"id": task_id})
        db.commit()
        
        return {"success": True, "message": f"Tarea '{current.titulo}' eliminada"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ OTRAS FUNCIONES ============

def get_tasks_by_priority(prioridad: str) -> List[Dict[str, Any]]:
    """Obtiene tareas por prioridad."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT t.*, p.name as project_name
            FROM tareas t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.prioridad = :prioridad
            ORDER BY t.fecha_entrega ASC
        """), {"prioridad": prioridad})
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_task_stats() -> Dict[str, Any]:
    """Obtiene estadísticas de tareas."""
    db = SessionLocal()
    try:
        total = db.execute(text("SELECT COUNT(*) as total FROM tareas")).fetchone()
        pendientes = db.execute(text("SELECT COUNT(*) as total FROM tareas WHERE estado = 'pendiente'")).fetchone()
        en_progreso = db.execute(text("SELECT COUNT(*) as total FROM tareas WHERE estado = 'en_progreso'")).fetchone()
        completadas = db.execute(text("SELECT COUNT(*) as total FROM tareas WHERE estado = 'completada'")).fetchone()
        
        return {
            "total": total.total if total else 0,
            "pendientes": pendientes.total if pendientes else 0,
            "en_progreso": en_progreso.total if en_progreso else 0,
            "completadas": completadas.total if completadas else 0
        }
    finally:
        db.close()
