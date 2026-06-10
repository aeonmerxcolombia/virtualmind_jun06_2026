from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.db import get_db
from app.models.competencia import Competencia
from app.schemas.competencia_schema import CompetenciaCreate, CompetenciaOut

router = APIRouter(
    prefix="/competencias",
    tags=["Competencias"]
)

# 🔄 Crear o actualizar (upsert)
@router.post("/", response_model=CompetenciaOut)
def crear_o_actualizar_competencia(competencia: CompetenciaCreate, db: Session = Depends(get_db)):
    db_comp = db.query(Competencia).filter(Competencia.user_id == competencia.user_id).first()
    if db_comp:
        # Si ya existe, actualizamos
        for key, value in competencia.dict(exclude_unset=True).items():
            setattr(db_comp, key, value)
        db.commit()
        db.refresh(db_comp)
        return db_comp
    else:
        # Si no existe, lo creamos
        nueva = Competencia(**competencia.model_dump())
        db.add(nueva)
        db.commit()
        db.refresh(nueva)
        return nueva

# 📥 Obtener todas las competencias
@router.get("/", response_model=List[CompetenciaOut])
def obtener_competencias(db: Session = Depends(get_db)):
    return db.query(Competencia).all()

# 📥 Obtener competencia por ID (UUID del registro)
@router.get("/{competencia_id}", response_model=CompetenciaOut)
def obtener_competencia(competencia_id: str, db: Session = Depends(get_db)):
    competencia = db.query(Competencia).filter(Competencia.id == competencia_id).first()
    if not competencia:
        raise HTTPException(status_code=404, detail="Competencia no encontrada")
    return competencia

# ✏️ Actualizar por ID (si necesitas actualizar por ID específico)
@router.put("/{competencia_id}", response_model=CompetenciaOut)
def actualizar_competencia(competencia_id: str, datos: CompetenciaCreate, db: Session = Depends(get_db)):
    competencia = db.query(Competencia).filter(Competencia.id == competencia_id).first()
    if not competencia:
        raise HTTPException(status_code=404, detail="Competencia no encontrada")
    for key, value in datos.model_dump().items():
        setattr(competencia, key, value)
    db.commit()
    db.refresh(competencia)
    return competencia

# 🗑 Eliminar competencia por ID
@router.delete("/{competencia_id}")
def eliminar_competencia(competencia_id: str, db: Session = Depends(get_db)):
    competencia = db.query(Competencia).filter(Competencia.id == competencia_id).first()
    if not competencia:
        raise HTTPException(status_code=404, detail="Competencia no encontrada")
    db.delete(competencia)
    db.commit()
    return {"message": "Competencia eliminada correctamente"}

# 📥 Obtener competencias por user_id (normalmente devuelve una sola por el upsert)
@router.get("/usuario/{user_id}", response_model=CompetenciaOut)
def obtener_competencias_usuario(user_id: str, db: Session = Depends(get_db)):
    comp = db.query(Competencia).filter(Competencia.user_id == user_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competencias no encontradas")
    return comp

# ✏️ Actualizar competencias por user_id
@router.post("/usuario/{user_id}", response_model=CompetenciaOut)
def actualizar_competencias_usuario(user_id: str, datos: CompetenciaCreate, db: Session = Depends(get_db)):
    datos_dict = datos.model_dump()
    datos_dict.pop('user_id', None)  # Quitar user_id del dict
    
    comp = db.query(Competencia).filter(Competencia.user_id == user_id).first()
    if comp:
        for key, value in datos_dict.items():
            setattr(comp, key, value)
        db.commit()
        db.refresh(comp)
        return comp
    else:
        nueva = Competencia(user_id=user_id, **datos_dict)
        db.add(nueva)
        db.commit()
        db.refresh(nueva)
        return nueva

