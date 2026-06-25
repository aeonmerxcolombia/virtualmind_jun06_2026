from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database.db import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.schemas.user_schema import UserCreate, UserOut, UserUpdate
from app.auth.hashing import Hash
from app.services.log_service import registrar_log
from app.auth.jwt_handler import verify_token
import uuid
from typing import List

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

    # Verificar email único
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
    db.commit()
    db.refresh(user)

    # Asignar roles
    roles = []
    for role_id in request.role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail=f"Rol con id {role_id} no encontrado")
        roles.append(role)
    user.roles = roles
    db.commit()
    db.refresh(user)

    registrar_log(
        db=db,
        usuario_id=uid_admin,
        tipo_evento="usuario_creado",
        descripcion=f"Usuario '{user.nombre}' creado con email {user.email}"
    )
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
# ACTUALIZAR USUARIO
# --------------------------
# --------------------------
# ACTUALIZAR USUARIO (PATCH)
# --------------------------
@router.patch("/{uid}", response_model=UserOut)
def update_user(uid: str, request: UserUpdate, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    uid_admin = token_data["user_id"]
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    data = request.dict(exclude_unset=True)

    # Campos simples
    for field in ["nombre", "tipo_documento", "documento", "email", "estado"]:
        if field in data:
            setattr(user, field, data[field])

    # Password solo si viene y no es vacío
    if "password" in data and data["password"]:
        user.password = Hash.encrypt(data["password"])

    # Roles si vienen
    if "role_ids" in data:
        new_roles = []
        for role_id in data["role_ids"]:
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail=f"Rol con id {role_id} no encontrado")
            new_roles.append(role)
        user.roles = new_roles

    db.commit()
    db.refresh(user)

    registrar_log(
        db=db,
        usuario_id=uid_admin,
        tipo_evento="usuario_actualizado",
        descripcion=f"Usuario '{user.nombre}' (UID {uid}) actualizado"
    )
    return user

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
    db.commit()
    db.refresh(user)

    registrar_log(
        db=db,
        usuario_id=uid_admin,
        tipo_evento="usuario_desactivado",
        descripcion=f"Usuario '{user.nombre}' (UID {uid}) fue desactivado"
    )
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

    registrar_log(
        db=db,
        usuario_id=uid_admin,
        tipo_evento="usuario_eliminado",
        descripcion=f"Usuario '{user.nombre}' (UID {uid}) fue eliminado permanentemente"
    )
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

    # Eliminar duplicados
    unique_permissions = {p.id: p.name for p in permissions}
    result_permissions = [{"id": pid, "name": name} for pid, name in sorted(unique_permissions.items())]

    return {"uid": uid, "roles": role_names, "permissions": result_permissions}

