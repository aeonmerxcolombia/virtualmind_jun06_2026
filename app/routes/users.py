# app/routes/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database.db import SessionLocal
from app.models.user import User
from app.models.role import Role
# --- CAMBIO 1: Importar el nuevo schema ---
from app.schemas.user_schema import (
    UserCreate, UserOut, UserUpdate, UserDeleteResponse, UserStatusUpdate,
    UserEmailUpdate # <-- AÑADIDO
)
from app.auth.hashing import Hash
from app.services.log_service import registrar_log
from app.auth.jwt_handler import verify_token
import uuid
from typing import List
from datetime import datetime

router = APIRouter(
    prefix="/users",
    tags=["Usuarios"]
)

# Dependencia para DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------
# VERIFICAR SI EMAIL EXISTE
# --------------------------
@router.get("/check-email")
def check_email_exists(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    return {"existe": user is not None}


# --------------------------
# LISTAR USUARIOS
# --------------------------
@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    return db.query(User).options(joinedload(User.roles)).all()


# --------------------------
# CREAR USUARIO
# --------------------------
@router.post("/", response_model=UserOut)
def create_user(request: UserCreate, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    uid_admin = token_data["user_id"]
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    user = User(
        uid=str(uuid.uuid4()),
        nombre=request.nombre,
        tipo_documento=request.tipo_documento,
        documento=request.documento,
        email=request.email,
        password=Hash.encrypt(request.password),
        estado=True
    )
    db.add(user)
    db.commit(); db.refresh(user) # Commit intermedio para que exista el user.uid
    roles = []
    for role_id in request.role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            # Revertir creación si un rol no existe? Podría ser.
            raise HTTPException(status_code=404, detail=f"Rol con id {role_id} no encontrado")
        roles.append(role)
    user.roles = roles
    db.commit(); db.refresh(user)
    registrar_log(db=db, usuario_id=uid_admin, tipo_evento="usuario_creado", descripcion=f"Usuario '{user.nombre}' creado con email {user.email}")
    return user


# --------------------------
# OBTENER USUARIO (SIN LOG)
# --------------------------
@router.get("/{uid}", response_model=UserOut)
def get_user(uid: str, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    user = db.query(User).options(joinedload(User.roles)).filter(User.uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# --------------------------
# ACTUALIZAR USUARIO (PATCH GENERAL)
# --------------------------
@router.patch("/{uid}", response_model=UserOut)
def update_user(uid: str, request: UserUpdate, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    uid_admin = token_data["user_id"]
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    data = request.dict(exclude_unset=True)

    # Nota: Este endpoint actual NO verifica si el email ya existe si se cambia aquí.
    # Es más seguro usar el endpoint dedicado /users/{uid}/email.
    for field in ["nombre", "tipo_documento", "documento", "email", "estado"]:
        if field in data:
            setattr(user, field, data[field])

    if "password" in data and data["password"]:
        user.password = Hash.encrypt(data["password"])

    if "role_ids" in data:
        new_roles = []
        for role_id in data["role_ids"]:
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail=f"Rol con id {role_id} no encontrado")
            new_roles.append(role)
        user.roles = new_roles

    try:
        db.commit()
        db.refresh(user)
        registrar_log(db=db, usuario_id=uid_admin, tipo_evento="usuario_actualizado", descripcion=f"Usuario '{user.nombre}' (UID {uid}) actualizado")
        return user
    except Exception as e:
        db.rollback()
        # Podría haber error si se intenta cambiar el email a uno existente aquí.
        if 'UNIQUE constraint failed: usuarios.email' in str(e):
             raise HTTPException(status_code=400, detail="El email proporcionado ya está en uso.")
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {e}")


# --- CAMBIO 2: AÑADIR NUEVO ENDPOINT PARA ACTUALIZAR SOLO EMAIL ---
@router.patch("/{uid}/email", response_model=UserOut, tags=["Usuarios"])
def update_user_email(
    uid: str,
    request: UserEmailUpdate, # Usa el nuevo schema específico
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token) # Protege la ruta
):
    """
    Actualiza únicamente el correo electrónico de un usuario específico.
    Incluye validación para asegurar que el nuevo email no esté en uso.
    """
    requesting_user_uid = token_data.get("user_id")
    # Opcional: Verifica si el usuario logueado es el mismo que se edita o un admin
    # if requesting_user_uid != uid and "superadmin" not in token_data.get("roles", []): # Ajusta según tus roles
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso denegado para cambiar este email")

    # 1. Buscar al usuario
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    new_email = request.email

    # 2. Verificar si el email realmente cambió
    if user.email == new_email:
        return user # No hay cambios, devolver el usuario actual

    # 3. CRÍTICO: Verificar que el NUEVO email no esté ya registrado por OTRO usuario
    existing_user = db.query(User).filter(User.email == new_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Error 400 (Bad Request) es apropiado aquí
            detail="El nuevo correo electrónico ya está registrado por otro usuario."
        )

    # 4. Actualizar el email
    try:
        user.email = new_email
        db.commit()
        db.refresh(user)

        # Opcional: Registrar el log del cambio de email
        registrar_log(
            db=db,
            usuario_id=requesting_user_uid, # Quién hizo el cambio
            tipo_evento="usuario_email_actualizado",
            descripcion=f"Email del usuario '{user.nombre}' (UID {uid}) actualizado a {new_email}"
        )

        return user # Devolver el objeto User actualizado
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el email en la base de datos: {str(e)}"
        )
# --- FIN DEL NUEVO ENDPOINT ---


# --------------------------
# DESACTIVAR USUARIO
# --------------------------
@router.delete("/{uid}")
def deactivate_user(uid: str, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    uid_admin = token_data["user_id"]
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.estado = False
    db.commit(); db.refresh(user)
    registrar_log(db=db, usuario_id=uid_admin, tipo_evento="usuario_desactivado", descripcion=f"Usuario '{user.nombre}' (UID {uid}) fue desactivado")
    return {"msg": "Usuario desactivado", "uid": uid}


# --------------------------
# ELIMINACIÓN PERMANENTE
# --------------------------
@router.delete("/hard/{uid}")
def delete_user(uid: str, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    uid_admin = token_data["user_id"]
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    registrar_log(db=db, usuario_id=uid_admin, tipo_evento="usuario_eliminado", descripcion=f"Usuario '{user.nombre}' (UID {uid}) fue eliminado permanentemente")
    return {"msg": "Usuario eliminado permanentemente", "uid": uid}


# --------------------------
# PERMISOS DEL USUARIO
# --------------------------
from app.models.permission import Permission
from app.models.role_permission import RolePermission

@router.get("/{uid}/permissions")
def get_user_permissions(uid: str, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    user = db.query(User).options(joinedload(User.roles)).filter(User.uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    role_ids = [role.id for role in user.roles]
    role_names = [role.name for role in user.roles]
    if not role_ids:
        return {"uid": uid, "roles": [], "permissions": []}
    permissions = (
        db.query(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id.in_(role_ids))
        .order_by(Permission.id)
        .all()
    )
    unique_permissions = {p.id: p.name for p in permissions}
    result_permissions = [{"id": pid, "name": name} for pid, name in sorted(unique_permissions.items())]
    return {"uid": uid, "roles": role_names, "permissions": result_permissions}


# -----------------------------------------------------
# --- ENDPOINT PARA ACEPTAR TÉRMINOS ---
# -----------------------------------------------------
@router.put("/me/accept-terms", status_code=status.HTTP_204_NO_CONTENT)
def accept_terms_for_current_user(db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    user_uid = token_data.get("user_id")
    if not user_uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = db.query(User).filter(User.uid == user_uid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if user.terms_accepted_at is not None:
        return
    try:
        user.terms_accepted_at = datetime.utcnow()
        db.add(user); db.commit(); db.refresh(user)
        return
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al actualizar BD: {e}")
