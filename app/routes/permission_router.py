# app/routes/permission_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.permission import Permission
from app.schemas.role_schema import PermissionCreate, PermissionOut

router = APIRouter(
    prefix="/permissions",
    tags=["Permisos"]
)

@router.post("/", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
def create_permission(data: PermissionCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo permiso.
    """
    if db.query(Permission).filter(Permission.name == data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permiso ya existe"
        )
    perm = Permission(name=data.name)
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm

@router.get("/", response_model=list[PermissionOut])
def list_permissions(db: Session = Depends(get_db)):
    """
    Listar todos los permisos.
    """
    return db.query(Permission).all()

@router.get("/{perm_id}", response_model=PermissionOut)
def get_permission(perm_id: int, db: Session = Depends(get_db)):
    """
    Obtener un permiso por ID.
    """
    perm = db.get(Permission, perm_id)
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado"
        )
    return perm

@router.put("/{perm_id}", response_model=PermissionOut)
def update_permission(perm_id: int, data: PermissionCreate, db: Session = Depends(get_db)):
    """
    Actualizar el nombre de un permiso existente.
    """
    perm = db.get(Permission, perm_id)
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado"
        )
    # Evitar duplicar nombres
    exists = (
        db.query(Permission)
          .filter(Permission.name == data.name, Permission.id != perm_id)
          .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe otro permiso con ese nombre"
        )
    perm.name = data.name
    db.commit()
    db.refresh(perm)
    return perm

@router.delete("/{perm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(perm_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un permiso por ID.
    """
    perm = db.get(Permission, perm_id)
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado"
        )
    db.delete(perm)
    db.commit()

