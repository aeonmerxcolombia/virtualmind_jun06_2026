from typing import Any, Dict, List
from sqlalchemy import text
from mcp_server.db import SessionLocal

def get_all_users(limit: int = 50) -> List[Dict[str, Any]]:
    """Obtiene todos los usuarios."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT uid, email, nombre, estado
            FROM usuarios 
            ORDER BY uid DESC 
            LIMIT :limit
        """), {"limit": limit})
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """Obtiene un usuario por ID."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT * FROM usuarios WHERE uid = :uid
        """), {"uid": user_id})
        
        row = result.fetchone()
        if not row:
            return {"error": "Usuario no encontrado"}
        
        user = dict(row._mapping)
        
        roles = db.execute(text("""
            SELECT r.name 
            FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_uid = :uid
        """), {"uid": user_id})
        user["roles"] = [dict(r._mapping)["name"] for r in roles]
        
        return user
    finally:
        db.close()

def search_users(query: str) -> List[Dict[str, Any]]:
    """Busca usuarios por nombre o email."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT uid, email, nombre, estado
            FROM usuarios 
            WHERE nombre LIKE :query OR email LIKE :query
            ORDER BY uid DESC
            LIMIT 20
        """), {"query": f"%{query}%"})
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_users_by_role(role_name: str) -> List[Dict[str, Any]]:
    """Obtiene usuarios por rol."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT u.uid, u.email, u.nombre, u.estado
            FROM usuarios u
            JOIN user_roles ur ON u.uid = ur.user_uid
            JOIN roles r ON r.id = ur.role_id
            WHERE r.name = :role
            ORDER BY u.uid DESC
        """), {"role": role_name})
        
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_all_roles() -> List[Dict[str, Any]]:
    """Obtiene todos los roles."""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT id, name FROM roles"))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

def get_role_permissions(role_id: int) -> Dict[str, Any]:
    """Obtiene permisos de un rol."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT p.name
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = :role_id
        """), {"role_id": role_id})
        
        return {"permissions": [dict(row._mapping) for row in result]}
    finally:
        db.close()

# ============ CREAR (CREATE) ============

def create_user(
    email: str,
    nombre: str,
    password: str = None,
    estado: int = 1,
    rol: str = "registrado",
    tipo_documento: str = "CC",
    documento: str = ""
) -> Dict[str, Any]:
    """Crea un nuevo usuario."""
    import uuid
    db = SessionLocal()
    try:
        user_id = str(uuid.uuid4())
        
        # Si no hay password, generar una
        if not password:
            password = uuid.uuid4().hex[:8]
        
        result = db.execute(text("""
            INSERT INTO usuarios (uid, email, password, nombre, estado, tipo_documento, documento)
            VALUES (:uid, :email, :password, :nombre, :estado, :tipo_documento, :documento)
        """), {
            "uid": user_id,
            "email": email,
            "password": password,
            "nombre": nombre,
            "estado": estado,
            "tipo_documento": tipo_documento,
            "documento": documento
        })
        
        # Asignar rol
        rol_row = db.execute(text("SELECT id FROM roles WHERE name = :name"), {"name": rol}).fetchone()
        if rol_row:
            db.execute(text("INSERT INTO user_roles (user_uid, role_id) VALUES (:uid, :role_id)"), 
                      {"uid": user_id, "role_id": rol_row.id})
        
        db.commit()
        return {"success": True, "user_id": user_id, "message": f"Usuario '{nombre}' creado"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ ACTUALIZAR (UPDATE) ============

def update_user(
    user_id: str,
    email: str = None,
    nombre: str = None,
    estado: int = None
) -> Dict[str, Any]:
    """Actualiza un usuario."""
    db = SessionLocal()
    try:
        updates = []
        params = {"uid": user_id}
        
        if email is not None:
            updates.append("email = :email")
            params["email"] = email
        if nombre is not None:
            updates.append("nombre = :nombre")
            params["nombre"] = nombre
        if estado is not None:
            updates.append("estado = :estado")
            params["estado"] = estado
        
        if not updates:
            return {"error": "No hay campos para actualizar"}
        
        query = f"UPDATE usuarios SET {', '.join(updates)} WHERE uid = :uid"
        db.execute(text(query), params)
        db.commit()
        
        return {"success": True, "message": f"Usuario {user_id} actualizado"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

def assign_role(user_id: str, rol: str) -> Dict[str, Any]:
    """Asigna un rol a un usuario."""
    db = SessionLocal()
    try:
        rol_row = db.execute(text("SELECT id FROM roles WHERE name = :name"), {"name": rol}).fetchone()
        if not rol_row:
            return {"error": f"Rol '{rol}' no encontrado"}
        
        # Verificar si ya tiene el rol
        existing = db.execute(text("""
            SELECT * FROM user_roles WHERE user_uid = :uid AND role_id = :role_id
        """), {"uid": user_id, "role_id": rol_row.id}).fetchone()
        
        if not existing:
            db.execute(text("INSERT INTO user_roles (user_uid, role_id) VALUES (:uid, :role_id)"), 
                      {"uid": user_id, "role_id": rol_row.id})
            db.commit()
        
        return {"success": True, "message": f"Rol '{rol}' asignado al usuario"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ ELIMINAR (DELETE) ============

def delete_user(user_id: str) -> Dict[str, Any]:
    """Elimina un usuario."""
    db = SessionLocal()
    try:
        # Verificar que existe
        current = db.execute(text("SELECT nombre FROM usuarios WHERE uid = :uid"), {"uid": user_id}).fetchone()
        if not current:
            return {"error": "Usuario no encontrado"}
        
        # Eliminar roles primero
        db.execute(text("DELETE FROM user_roles WHERE user_uid = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM usuarios WHERE uid = :uid"), {"uid": user_id})
        db.commit()
        
        return {"success": True, "message": f"Usuario '{current.nombre}' eliminado"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# ============ OTRAS FUNCIONES ============

def get_active_users() -> List[Dict[str, Any]]:
    """Obtiene usuarios activos."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT uid, email, nombre, estado FROM usuarios WHERE estado = 1
        """))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()
