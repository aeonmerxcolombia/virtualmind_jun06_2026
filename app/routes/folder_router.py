# app/routes/folder_router.py

from fastapi import (
    APIRouter, Depends,
    HTTPException, status, Query
)
from sqlalchemy.orm import Session
from typing import List

from app.database.db import SessionLocal
from app.auth.deps import get_current_user
from app.models.folder import Folder
from app.schemas.folder_schema import (
    FolderCreate, FolderOut, FolderUpdate
)

router = APIRouter(prefix="/folders", tags=["Folders"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "/",
    response_model=List[FolderOut],
    summary="Listar carpetas",
    description="Devuelve carpetas globales y propias del usuario"
)
def list_folders(
    include_general: bool = Query(
        True,
        title="Incluir generales",
        description="Si es true, incluye carpetas globales (subido_por_uid IS NULL)"
    ),
    db: Session = Depends(get_db),
    token: dict = Depends(get_current_user)
):
    uid = token["user_id"]
    q = db.query(Folder)
    if include_general:
        q = q.filter(
            (Folder.subido_por_uid == None) |
            (Folder.subido_por_uid == uid)
        )
    else:
        q = q.filter(Folder.subido_por_uid == uid)
    return q.order_by(Folder.fecha_creado.desc()).all()


@router.post(
    "/",
    response_model=FolderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear carpeta",
    description="Crea una carpeta personal; `subido_por_uid` = mí user_id"
)
def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(get_current_user)
):
    uid = token["user_id"]
    folder = Folder(
        nombre         = data.nombre,
        descripcion    = data.descripcion,
        parent_id      = data.parent_id,
        subido_por_uid = uid
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.get(
    "/{folder_id}",
    response_model=FolderOut,
    summary="Obtener carpeta",
    description="Devuelve datos de una carpeta (si es global o mía)"
)
def get_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(get_current_user)
):
    uid = token["user_id"]
    folder = db.query(Folder).get(folder_id)
    if not folder or (
       folder.subido_por_uid is not None and folder.subido_por_uid != uid
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpeta no encontrada"
        )
    return folder


@router.put(
    "/{folder_id}",
    response_model=FolderOut,
    summary="Actualizar carpeta",
    description="Modifica nombre, descripción, parent o estado"
)
def update_folder(
    folder_id: int,
    data: FolderUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(get_current_user)
):
    uid = token["user_id"]
    folder = db.query(Folder).get(folder_id)
    if not folder or (
       folder.subido_por_uid is not None and folder.subido_por_uid != uid
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpeta no encontrada"
        )
    # Aplicar cambios desde el body
    for field, value in data.dict(exclude_unset=True).items():
        setattr(folder, field, value)
    db.commit()
    db.refresh(folder)
    return folder


@router.delete(
    "/{folder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar carpeta",
    description="Marca la carpeta `estado=False` (no la borra físicamente)"
)
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(get_current_user)
):
    uid = token["user_id"]
    folder = db.query(Folder).get(folder_id)
    if not folder or (
       folder.subido_por_uid is not None and folder.subido_por_uid != uid
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpeta no encontrada"
        )
    folder.estado = False
    db.commit()
    # No devolvemos body (204)

