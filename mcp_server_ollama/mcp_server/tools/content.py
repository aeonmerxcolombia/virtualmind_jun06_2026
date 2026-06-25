from typing import Any, Dict, List
from sqlalchemy import text
from mcp_server.db import SessionLocal

def get_documents_by_project(project_id: int) -> List[Dict[str, Any]]:
    """Obtiene documentos de un proyecto."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT * FROM documents 
            WHERE project_id = :project_id
            ORDER BY id DESC
        """), {"project_id": project_id})
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_all_documents(limit: int = 50) -> List[Dict[str, Any]]:
    """Obtiene todos los documentos."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT d.*, p.name as project_name
            FROM documents d
            LEFT JOIN projects p ON d.project_id = p.id
            ORDER BY d.id DESC
            LIMIT :limit
        """), {"limit": limit})
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_document_by_id(doc_id: int) -> Dict[str, Any]:
    """Obtiene un documento por ID."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT d.*, p.name as project_name
            FROM documents d
            LEFT JOIN projects p ON d.project_id = p.id
            WHERE d.id = :id
        """), {"id": doc_id})
        row = result.fetchone()
        return dict(row._mapping) if row else {"error": "Documento no encontrado"}
    finally:
        db.close()

def get_fases() -> List[Dict[str, Any]]:
    """Obtiene todas las fases."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT * FROM fases ORDER BY id"))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_fase_by_id(fase_id: int) -> Dict[str, Any]:
    """Obtiene una fase por ID con sus proyectos."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT * FROM fases WHERE id = :id"), {"id": fase_id})
        row = result.fetchone()
        if not row:
            return {"error": "Fase no encontrada"}
        
        fase = dict(row._mapping)
        
        proyectos = db.execute(text("""
            SELECT id, name, estado, start_date, end_date
            FROM projects WHERE fase_id = :fase_id
        """), {"fase_id": fase_id})
        fase["proyectos"] = [dict(p._mapping) for p in proyectos]
        
        return fase
    finally:
        db.close()

def get_etapas() -> List[Dict[str, Any]]:
    """Obtiene todas las etapas."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT * FROM etapas ORDER BY id"))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_cronograma_by_project(project_id: int) -> Dict[str, Any]:
    """Obtiene el cronograma de un proyecto."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT * FROM cronogramas WHERE project_id = :project_id
        """), {"project_id": project_id})
        row = result.fetchone()
        return dict(row._mapping) if row else {"error": "Cronograma no encontrado"}
    finally:
        db.close()

def get_modules_by_course(course_id: int) -> List[Dict[str, Any]]:
    """Obtiene módulos de un curso."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT * FROM modules WHERE course_id = :course_id ORDER BY orden
        """), {"course_id": course_id})
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_units_by_module(module_id: int) -> List[Dict[str, Any]]:
    """Obtiene unidades de un módulo."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT * FROM units WHERE module_id = :module_id ORDER BY orden
        """), {"module_id": module_id})
        return [dict(row._mapping) for row in result]
    finally:
        db.close()
