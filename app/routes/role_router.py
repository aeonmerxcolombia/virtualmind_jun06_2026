# app/routes/role_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload  # Importa joinedload
from app.database.db import get_db
from app.models.role       import Role
from app.models.permission import Permission   # ← Import correcto
from app.schemas.role_schema import RoleCreate, RoleOut

router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)

@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(data: RoleCreate, db: Session = Depends(get_db)):
    # Verificar que el rol no exista
    if db.query(Role).filter(Role.name == data.name).first():
        raise HTTPException(status_code=400, detail="Rol ya existe")

    # Validar permisos
    perms = db.query(Permission).filter(Permission.id.in_(data.permission_ids)).all()
    if len(perms) != len(set(data.permission_ids)):
        raise HTTPException(status_code=400, detail="Algún permission_id no es válido")

    role = Role(name=data.name)
    role.permissions = perms

    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.get("/", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    """
    Listar todos los roles junto a sus permisos.
    """
    return db.query(Role).options(joinedload(Role.permissions)).all()

@router.get("/{role_id}", response_model=RoleOut)
def get_role(role_id: int, db: Session = Depends(get_db)):
    """
    Obtener un rol por su ID.
    """
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return role

@router.put("/{role_id}", response_model=RoleOut)
def update_role(role_id: int, data: RoleCreate, db: Session = Depends(get_db)):
    """
    Actualizar nombre y permisos de un rol existente.
    """
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    perms = db.query(Permission).filter(Permission.id.in_(data.permission_ids)).all()
    if len(perms) != len(set(data.permission_ids)):
        raise HTTPException(status_code=400, detail="Algún permission_id no es válido")

    role.name = data.name
    role.permissions = perms
    db.commit()
    db.refresh(role)
    return role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un rol por su ID.
    """
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    db.delete(role)
    db.commit()


