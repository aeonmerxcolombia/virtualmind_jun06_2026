# app/routes/unit_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.unit import Unit
from app.schemas import unit_schema  # Asegúrate de que la ruta de importación sea correcta

router = APIRouter(
    prefix="/units",
    tags=["units"]
)

@router.post("/", response_model=unit_schema.UnitRead)
def create_unit(unit: unit_schema.UnitCreate, db: Session = Depends(get_db)):
    db_unit = Unit(**unit.model_dump())
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit

@router.get("/module/{module_id}", response_model=List[unit_schema.UnitRead])
def get_units_by_module(module_id: int, db: Session = Depends(get_db)):
    units = db.query(Unit).filter(Unit.module_id == module_id).all()
    return units

@router.get("/{unit_id}", response_model=unit_schema.UnitRead)
def get_unit(unit_id: int, db: Session = Depends(get_db)):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return unit

@router.put("/{unit_id}", response_model=unit_schema.UnitRead)
def update_unit(unit_id: int, unit: unit_schema.UnitUpdate, db: Session = Depends(get_db)):
    db_unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    # exclude_unset=True es clave para solo actualizar los campos proporcionados
    for var, value in unit.dict(exclude_unset=True).items(): 
        setattr(db_unit, var, value)
    db.commit()
    db.refresh(db_unit)
    return db_unit

@router.delete("/{unit_id}")
def delete_unit(unit_id: int, db: Session = Depends(get_db)):
    db_unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    db.delete(db_unit)
    db.commit()
    return {"detail": "Unidad eliminada"}

@router.get("/", response_model=List[unit_schema.UnitRead])
def get_all_units(db: Session = Depends(get_db)):
    """
    Obtiene la lista de TODAS las unidades, con sus datos completos.
    """
    units = db.query(Unit).all()
    return units
