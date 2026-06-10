# app/routers/fase_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.fase import Fase
from app.schemas.fase_schema import FaseRead, FaseCreate, FaseUpdate, ReorderRequest

router = APIRouter(
    prefix="/fases",
    tags=["fases"]
)

# -------------------- CREATE --------------------
@router.post("/", response_model=FaseRead)
async def create_fase(fase: FaseCreate, db: Session = Depends(get_db)):
    if fase.orden is None:
        max_orden_result = db.query(Fase.orden).order_by(Fase.orden.desc()).first()
        nuevo_orden = (max_orden_result[0] + 1) if max_orden_result and max_orden_result[0] is not None else 0
    else:
        nuevo_orden = fase.orden

    nueva_fase = Fase(nombre=fase.nombre, descripcion=fase.descripcion, orden=nuevo_orden)
    db.add(nueva_fase)
    db.commit()
    db.refresh(nueva_fase)
    return nueva_fase

# -------------------- READ (list) --------------------
@router.get("/", response_model=List[FaseRead])
def list_fases(db: Session = Depends(get_db)):
    return db.query(Fase).order_by(Fase.orden).all()

# -------------------- READ (detail) --------------------
@router.get("/{fase_id}", response_model=FaseRead)
def get_fase(fase_id: int, db: Session = Depends(get_db)):
    fase = db.query(Fase).filter(Fase.id == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase no encontrada")
    return fase

# -------------------- REORDER (RUTA ESPECÍFICA) --------------------
# Esta ruta debe ir PRIMERO para que no sea capturada por la ruta dinámica de abajo.
@router.put("/reorder", status_code=status.HTTP_204_NO_CONTENT)
def reorder_fases(request: ReorderRequest, db: Session = Depends(get_db)):
    """
    Reordena las fases según el orden de los IDs proporcionados.
    """
    fases_existentes = db.query(Fase).filter(Fase.id.in_(request.ids)).all()
    if len(fases_existentes) != len(set(request.ids)):
        raise HTTPException(status_code=400, detail="Uno o más IDs de fase no existen.")

    orden_map = {fase_id: index for index, fase_id in enumerate(request.ids)}

    for fase_id, nuevo_orden in orden_map.items():
        db.query(Fase).filter(Fase.id == fase_id).update({Fase.orden: nuevo_orden})

    db.commit()

# -------------------- UPDATE (RUTA DINÁMICA) --------------------
# Esta ruta va DESPUÉS de cualquier otra ruta PUT más específica.
@router.put("/{fase_id}", response_model=FaseRead)
async def update_fase(fase_id: int, data: FaseUpdate, db: Session = Depends(get_db)):
    fase = db.query(Fase).filter(Fase.id == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase no encontrada")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(fase, key, value)

    db.commit()
    db.refresh(fase)
    return fase

# -------------------- DELETE --------------------
@router.delete("/{fase_id}")
def delete_fase(fase_id: int, db: Session = Depends(get_db)):
    fase = db.query(Fase).filter(Fase.id == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase no encontrada")
    db.delete(fase)
    db.commit()
    return {"ok": True}
