from typing import Any, Dict, List
from sqlalchemy import text
from mcp_server.db import SessionLocal
from mcp_server.tools.ai import generate_json_with_ai, generate_with_ai

def get_all_clients(limit: int = 50) -> List[Dict[str, Any]]:
    """Obtiene todos los clientes."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT c.*, u.email, u.nombre as nombre_contacto
            FROM client_profiles c
            LEFT JOIN usuarios u ON c.user_id = u.uid
            ORDER BY c.id DESC
            LIMIT :limit
        """), {"limit": limit})
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_client_by_id(client_id: str) -> Dict[str, Any]:
    """Obtiene un cliente por ID."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT c.*, u.email, u.nombre as nombre_contacto
            FROM client_profiles c
            LEFT JOIN usuarios u ON c.user_id = u.uid
            WHERE c.id = :id
        """), {"id": client_id})
        
        row = result.fetchone()
        if not row:
            return {"error": "Cliente no encontrado"}
        
        client = dict(row._mapping)
        
        proyectos = db.execute(text("""
            SELECT id, name, estado, start_date, end_date
            FROM projects WHERE client_id = :client_id
            ORDER BY id DESC
        """), {"client_id": client.get("user_id")})
        client["proyectos"] = [dict(p._mapping) for p in proyectos]
        
        return client
    finally:
        db.close()

def get_clients_with_active_projects() -> List[Dict[str, Any]]:
    """Obtiene clientes con proyectos activos."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT DISTINCT c.id, c.razon_social, u.email, u.nombre as nombre_contacto,
                   (SELECT COUNT(*) FROM projects p WHERE p.client_id = c.user_id AND p.estado = 'En Desarrollo') as proyectos_activos
            FROM client_profiles c
            LEFT JOIN usuarios u ON c.user_id = u.uid
            HAVING proyectos_activos > 0
            ORDER BY proyectos_activos DESC
        """))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def analyze_client_with_ai(client_id: str) -> Dict[str, Any]:
    """Analiza un cliente con IA."""
    client = get_client_by_id(client_id)
    
    if "error" in client:
        return client
    
    prompt = f"""Analiza el siguiente cliente y sus proyectos:

Empresa: {client.get('razon_social')}
Contacto: {client.get('nombre_contacto')}
Email: {client.get('email')}
Proyectos: {len(client.get('proyectos', []))}

Lista de proyectos:
{chr(10).join([f"- {p.get('name')}: {p.get('estado')}" for p in client.get('proyectos', [])])}

Responde en JSON:
{{
    "resumen": "Resumen del cliente",
    "proyectos_activos": 0,
    "proyectos_completados": 0,
    "recomendaciones": ["rec1"],
    "estado_general": "activo/inactivo/potencial"
}}"""
    
    return generate_json_with_ai(
        prompt=prompt,
        system_instruction="Eres un experto en gestión de clientes y proyectos."
    )

# ============ CREAR (CREATE) ============

def create_client(
    razon_social: str,
    nit: str = "",
    user_id: str = None,
    tipo_entidad: str = "Privada",
    direccion: str = "",
    ciudad: str = "",
    pais: str = "Colombia",
    caracter_entidad: str = "",
    email_contacto: str = ""
) -> Dict[str, Any]:
    """Crea un nuevo cliente."""
    import uuid
    db = SessionLocal()
    try:
        client_id = str(uuid.uuid4())
        
        result = db.execute(text("""
            INSERT INTO client_profiles 
            (id, user_id, razon_social, nit, tipo_entidad, direccion, ciudad, pais, caracter_entidad)
            VALUES (:id, :user_id, :razon_social, :nit, :tipo_entidad, :direccion, :ciudad, :pais, :caracter_entidad)
        """), {
            "id": client_id,
            "user_id": user_id,
            "razon_social": razon_social,
            "nit": nit,
            "tipo_entidad": tipo_entidad,
            "direccion": direccion,
            "ciudad": ciudad,
            "pais": pais,
            "caracter_entidad": caracter_entidad
        })
        
        db.commit()
        return {"success": True, "client_id": client_id, "message": f"Cliente '{razon_social}' creado"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ ACTUALIZAR (UPDATE) ============

def update_client(
    client_id: str,
    razon_social: str = None,
    nit: str = None,
    tipo_entidad: str = None,
    direccion: str = None,
    ciudad: str = None,
    pais: str = None
) -> Dict[str, Any]:
    """Actualiza un cliente."""
    db = SessionLocal()
    try:
        updates = []
        params = {"id": client_id}
        
        if razon_social is not None:
            updates.append("razon_social = :razon_social")
            params["razon_social"] = razon_social
        if nit is not None:
            updates.append("nit = :nit")
            params["nit"] = nit
        if tipo_entidad is not None:
            updates.append("tipo_entidad = :tipo_entidad")
            params["tipo_entidad"] = tipo_entidad
        if direccion is not None:
            updates.append("direccion = :direccion")
            params["direccion"] = direccion
        if ciudad is not None:
            updates.append("ciudad = :ciudad")
            params["ciudad"] = ciudad
        if pais is not None:
            updates.append("pais = :pais")
            params["pais"] = pais
        
        if not updates:
            return {"error": "No hay campos para actualizar"}
        
        query = f"UPDATE client_profiles SET {', '.join(updates)} WHERE id = :id"
        db.execute(text(query), params)
        db.commit()
        
        return {"success": True, "message": f"Cliente {client_id} actualizado"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ ELIMINAR (DELETE) ============

def delete_client(client_id: str) -> Dict[str, Any]:
    """Elimina un cliente."""
    db = SessionLocal()
    try:
        current = db.execute(text("SELECT razon_social FROM client_profiles WHERE id = :id"), {"id": client_id}).fetchone()
        if not current:
            return {"error": "Cliente no encontrado"}
        
        db.execute(text("DELETE FROM client_profiles WHERE id = :id"), {"id": client_id})
        db.commit()
        
        return {"success": True, "message": f"Cliente '{current.razon_social}' eliminado"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ OTRAS FUNCIONES ============

def search_clients(query: str) -> List[Dict[str, Any]]:
    """Busca clientes por razón social, NIT o nombre de contacto."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT c.id, c.user_id, c.razon_social, c.nit, c.ciudad, c.tipo_entidad,
                   u.email, u.nombre as nombre_contacto
            FROM client_profiles c
            LEFT JOIN usuarios u ON c.user_id = u.uid
            WHERE c.razon_social LIKE :q OR c.nit LIKE :q OR u.nombre LIKE :q
            ORDER BY c.razon_social
            LIMIT 10
        """), {"q": f"%{query}%"})
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_clients_by_city(ciudad: str) -> List[Dict[str, Any]]:
    """Obtiene clientes por ciudad."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT c.id, c.razon_social, c.ciudad, c.tipo_entidad, u.email
            FROM client_profiles c
            LEFT JOIN usuarios u ON c.user_id = u.uid
            WHERE c.ciudad LIKE :ciudad
        """), {"ciudad": f"%{ciudad}%"})
        return [dict(row._mapping) for row in result]
    finally:
        db.close()
