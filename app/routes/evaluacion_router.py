from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.evaluacion import Evaluacion
from app.schemas.evaluacion_schema import EvaluacionCreate, EvaluacionOut
import uuid
import json

router = APIRouter(
    prefix="/evaluaciones",
    tags=["Evaluaciones"]
)

# Crear una evaluación
@router.post("/", response_model=EvaluacionOut)
def crear_evaluacion(evaluacion: EvaluacionCreate, db: Session = Depends(get_db)):
    data = evaluacion.model_dump()
    # Convertir UUID a string (si fuera UUID, pero si ya viene como string no pasa nada)
    data["creador_id"] = str(data["creador_id"])
    # Si tipos_pregunta o parametros vinieran como string en vez de list/dict
    if isinstance(data["tipos_pregunta"], str):
        data["tipos_pregunta"] = json.loads(data["tipos_pregunta"])
    if isinstance(data.get("parametros"), str):
        data["parametros"] = json.loads(data["parametros"])
    db_eval = Evaluacion(
        id=str(uuid.uuid4()),
        **data
    )
    db.add(db_eval)
    db.commit()
    db.refresh(db_eval)
    return db_eval

# Listar todas las evaluaciones
@router.get("/", response_model=list[EvaluacionOut])
def listar_evaluaciones(db: Session = Depends(get_db)):
    return db.query(Evaluacion).all()

# Obtener evaluación por ID
@router.get("/{evaluacion_id}", response_model=EvaluacionOut)
def obtener_evaluacion(evaluacion_id: str, db: Session = Depends(get_db)):
    eval = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
    if not eval:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    return eval

# Actualizar evaluación por ID
@router.put("/{evaluacion_id}", response_model=EvaluacionOut)
def actualizar_evaluacion(evaluacion_id: str, datos: EvaluacionCreate, db: Session = Depends(get_db)):
    eval = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
    if not eval:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    data = datos.model_dump()
    data["creador_id"] = str(data["creador_id"])
    if isinstance(data["tipos_pregunta"], str):
        data["tipos_pregunta"] = json.loads(data["tipos_pregunta"])
    if isinstance(data.get("parametros"), str):
        data["parametros"] = json.loads(data["parametros"])
    for key, value in data.items():
        setattr(eval, key, value)
    db.commit()
    db.refresh(eval)
    return eval

# Eliminar evaluación por ID
@router.delete("/{evaluacion_id}")
def eliminar_evaluacion(evaluacion_id: str, db: Session = Depends(get_db)):
    eval = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
    if not eval:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    db.delete(eval)
    db.commit()
    return {"message": "Evaluación eliminada correctamente"}

