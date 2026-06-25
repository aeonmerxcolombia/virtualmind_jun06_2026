import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.db import get_db
from app.models.project import Project
from app.models.fase import Fase   # 👈 Importamos el modelo Fase
from app.schemas.project_schema import ProjectRead, ProjectCreate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    proyecto_data = project_in.model_dump()

    # Convertir lista a JSON string para almacenar en DB
    if proyecto_data.get("publico_objetivo") is not None:
        proyecto_data["publico_objetivo"] = json.dumps(proyecto_data["publico_objetivo"])

    # Validar que la fase exista si se envía fase_id
    if proyecto_data.get("fase_id") is not None:
        fase = db.query(Fase).filter(Fase.id == proyecto_data["fase_id"]).first()
        if not fase:
            raise HTTPException(status_code=400, detail="La fase especificada no existe")

    db_project = Project(**proyecto_data)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Parsear publico_objetivo para la respuesta
    if db_project.publico_objetivo:
        try:
            db_project.publico_objetivo = json.loads(db_project.publico_objetivo)
        except Exception:
            db_project.publico_objetivo = []

    return db_project


@router.get("/", response_model=List[ProjectRead])
def list_projects(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fase_id: Optional[int] = Query(None, description="Filtrar por fase_id"),
    db: Session = Depends(get_db)
):
    query = db.query(Project)
    if estado:
        query = query.filter(Project.estado == estado)
    if fase_id:
        query = query.filter(Project.fase_id == fase_id)

    projects = query.order_by(Project.id.desc()).all()
    for p in projects:
        if p.publico_objetivo:
            try:
                p.publico_objetivo = json.loads(p.publico_objetivo)
            except Exception:
                p.publico_objetivo = []
    return projects


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if project.publico_objetivo:
        try:
            project.publico_objetivo = json.loads(project.publico_objetivo)
        except Exception:
            project.publico_objetivo = []
    return project


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, updated: ProjectCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    updated_data = updated.dict(exclude_unset=True)

    # Validar fase si viene en actualización
    if "fase_id" in updated_data and updated_data["fase_id"] is not None:
        fase = db.query(Fase).filter(Fase.id == updated_data["fase_id"]).first()
        if not fase:
            raise HTTPException(status_code=400, detail="La fase especificada no existe")

    if "publico_objetivo" in updated_data and updated_data["publico_objetivo"] is not None:
        updated_data["publico_objetivo"] = json.dumps(updated_data["publico_objetivo"])

    for key, value in updated_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)

    if project.publico_objetivo:
        try:
            project.publico_objetivo = json.loads(project.publico_objetivo)
        except Exception:
            project.publico_objetivo = []

    return project


@router.patch("/{project_id}/estado", response_model=ProjectRead)
def cambiar_estado_proyecto(project_id: int, nuevo_estado: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project.estado = nuevo_estado
    db.commit()
    db.refresh(project)

    if project.publico_objetivo:
        try:
            project.publico_objetivo = json.loads(project.publico_objetivo)
        except Exception:
            project.publico_objetivo = []

    return project


@router.patch("/{project_id}/fase", response_model=ProjectRead)
def cambiar_fase_proyecto(project_id: int, nueva_fase_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Validar que la nueva fase exista
    fase = db.query(Fase).filter(Fase.id == nueva_fase_id).first()
    if not fase:
        raise HTTPException(status_code=400, detail="La fase especificada no existe")

    project.fase_id = nueva_fase_id
    db.commit()
    db.refresh(project)

    if project.publico_objetivo:
        try:
            project.publico_objetivo = json.loads(project.publico_objetivo)
        except Exception:
            project.publico_objetivo = []

    return project

