from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.learning_activity import LearningActivity
from app.schemas.learning_activity_schema import (
    LearningActivityCreate,
    LearningActivityUpdate,
    LearningActivityOut,
)

router = APIRouter(
    prefix="/learning_activities",
    tags=["Actividades de Aprendizaje"]
)

# Crear actividad
@router.post("/", response_model=LearningActivityOut)
def create_learning_activity(activity: LearningActivityCreate, db: Session = Depends(get_db)):
    la = LearningActivity(**activity.model_dump())
    db.add(la)
    db.commit()
    db.refresh(la)
    return la

# Listar todas las actividades
@router.get("/", response_model=list[LearningActivityOut])
def list_activities(db: Session = Depends(get_db)):
    return db.query(LearningActivity).all()

# Listar actividades por unidad
@router.get("/unit/{unit_id}", response_model=list[LearningActivityOut])
def list_activities_by_unit(unit_id: int, db: Session = Depends(get_db)):
    return db.query(LearningActivity).filter(LearningActivity.unit_id == unit_id).all()

# Obtener actividad por ID
@router.get("/{activity_id}", response_model=LearningActivityOut)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    la = db.query(LearningActivity).filter(LearningActivity.id == activity_id).first()
    if not la:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return la

# Actualizar actividad
@router.put("/{activity_id}", response_model=LearningActivityOut)
def update_activity(activity_id: int, data: LearningActivityUpdate, db: Session = Depends(get_db)):
    la = db.query(LearningActivity).filter(LearningActivity.id == activity_id).first()
    if not la:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(la, k, v)
    db.commit()
    db.refresh(la)
    return la

# Eliminar actividad
@router.delete("/{activity_id}")
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    la = db.query(LearningActivity).filter(LearningActivity.id == activity_id).first()
    if not la:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    db.delete(la)
    db.commit()
    return {"ok": True}

