from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from app.database.db import get_db
from app.models.tarea_ia import TareaIA

router = APIRouter(prefix="/tareas-ia", tags=["tareas-ia"])

class TareaIACreate(BaseModel):
    descripcion: str
    prioridad: str = "medium"
    categoria: str = "other"
    notas: Optional[str] = None
    responsable: str = "backend"

class TareaIAUpdate(BaseModel):
    descripcion: Optional[str] = None
    prioridad: Optional[str] = None
    categoria: Optional[str] = None
    estado: Optional[str] = None
    notas: Optional[str] = None
    responsable: Optional[str] = None

class TareaIAOut(BaseModel):
    id: int
    descripcion: str
    prioridad: str
    categoria: str
    estado: str
    responsable: str
    notas: Optional[str]
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    @field_validator('fecha_creacion', 'fecha_actualizacion', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return v

@router.get("/", response_model=List[TareaIAOut])
def list_tareas_ia(db: Session = Depends(get_db)):
    tareas = db.query(TareaIA).order_by(TareaIA.id.desc()).all()
    return tareas

@router.post("/", response_model=TareaIAOut)
def create_tarea_ia(tarea: TareaIACreate, db: Session = Depends(get_db)):
    db_tarea = TareaIA(
        descripcion=tarea.descripcion,
        prioridad=tarea.prioridad,
        categoria=tarea.categoria,
        notas=tarea.notas,
        responsable=tarea.responsable
    )
    db.add(db_tarea)
    db.commit()
    db.refresh(db_tarea)
    return db_tarea

@router.put("/{tarea_id}", response_model=TareaIAOut)
def update_tarea_ia(tarea_id: int, tarea: TareaIAUpdate, db: Session = Depends(get_db)):
    db_tarea = db.query(TareaIA).filter(TareaIA.id == tarea_id).first()
    if not db_tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if tarea.descripcion is not None:
        db_tarea.descripcion = tarea.descripcion
    if tarea.prioridad is not None:
        db_tarea.prioridad = tarea.prioridad
    if tarea.categoria is not None:
        db_tarea.categoria = tarea.categoria
    if tarea.estado is not None:
        db_tarea.estado = tarea.estado
    if tarea.notas is not None:
        db_tarea.notas = tarea.notas
    if tarea.responsable is not None:
        db_tarea.responsable = tarea.responsable
    
    db.commit()
    db.refresh(db_tarea)
    return db_tarea

@router.delete("/{tarea_id}")
def delete_tarea_ia(tarea_id: int, db: Session = Depends(get_db)):
    db_tarea = db.query(TareaIA).filter(TareaIA.id == tarea_id).first()
    if not db_tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    db.delete(db_tarea)
    db.commit()
    return {"message": "Tarea eliminada"}

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(TareaIA).count()
    pending = db.query(TareaIA).filter(TareaIA.estado == "pending").count()
    in_progress = db.query(TareaIA).filter(TareaIA.estado == "in_progress").count()
    completed = db.query(TareaIA).filter(TareaIA.estado == "completed").count()
    
    # Stats por responsable
    backend = db.query(TareaIA).filter(TareaIA.responsable == "backend").count()
    frontend = db.query(TareaIA).filter(TareaIA.responsable == "frontend").count()
    qa = db.query(TareaIA).filter(TareaIA.responsable == "qa").count()
    
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "by_responsable": {
            "backend": backend,
            "frontend": frontend,
            "qa": qa
        }
    }

@router.get("/filter/{responsable}")
def filter_by_responsable(responsable: str, db: Session = Depends(get_db)):
    tareas = db.query(TareaIA).filter(TareaIA.responsable == responsable).order_by(TareaIA.id.desc()).all()
    return tareas
