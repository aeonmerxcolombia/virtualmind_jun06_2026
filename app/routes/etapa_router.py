# app/routers/etapa_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.etapa import Etapa
from app.models.fase import Fase
from app.schemas.etapa_schema import EtapaRead, EtapaCreate, EtapaUpdate, ReorderRequest

router = APIRouter(
    prefix="/etapas",
    tags=["etapas"]
)

# -------------------- CREATE --------------------
@router.post("/", response_model=EtapaRead)
async def create_etapa(etapa: EtapaCreate, db: Session = Depends(get_db)):
    fase_exists = db.query(Fase).filter(Fase.id == etapa.fase_id).first()
    if not fase_exists:
        raise HTTPException(status_code=400, detail="Fase indicada no existe")

    if etapa.orden is None:
        max_orden_result = db.query(Etapa.orden).filter(Etapa.fase_id == etapa.fase_id).order_by(Etapa.orden.desc()).first()
        nuevo_orden = (max_orden_result[0] + 1) if max_orden_result and max_orden_result[0] is not None else 0
    else:
        nuevo_orden = etapa.orden

    nueva_etapa = Etapa(
        nombre=etapa.nombre,
        descripcion=etapa.descripcion,
        orden=nuevo_orden,
        fase_id=etapa.fase_id
    )
    db.add(nueva_etapa)
    db.commit()
    db.refresh(nueva_etapa)
    return nueva_etapa

# -------------------- READ (list) --------------------
@router.get("/", response_model=List[EtapaRead])
def list_etapas(db: Session = Depends(get_db)):
    return db.query(Etapa).order_by(Etapa.fase_id, Etapa.orden).all()

# -------------------- READ (detail) --------------------
@router.get("/{etapa_id}", response_model=EtapaRead)
def get_etapa(etapa_id: int, db: Session = Depends(get_db)):
    etapa = db.query(Etapa).filter(Etapa.id == etapa_id).first()
    if not etapa:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    return etapa

# -------------------- REORDER (RUTA ESPECÍFICA - MOVIDA AQUÍ ARRIBA) --------------------
@router.put("/reorder", status_code=status.HTTP_204_NO_CONTENT) # <-- CORRECCIÓN: Era 204, no 24
def reorder_etapas(request: ReorderRequest, db: Session = Depends(get_db)):
    """
    Reordena las etapas según el orden de los IDs proporcionados.
    """
    etapas_existentes = db.query(Etapa).filter(Etapa.id.in_(request.ids)).all()
    if len(etapas_existentes) != len(set(request.ids)):
        raise HTTPException(status_code=400, detail="Uno o más IDs de etapa no existen.")

    orden_map = {etapa_id: index for index, etapa_id in enumerate(request.ids)}

    for etapa_id, nuevo_orden in orden_map.items():
        db.query(Etapa).filter(Etapa.id == etapa_id).update({Etapa.orden: nuevo_orden})

    db.commit()

# -------------------- UPDATE (RUTA DINÁMICA - AHORA DESPUÉS DE REORDER) --------------------
@router.put("/{etapa_id}", response_model=EtapaRead)
async def update_etapa(etapa_id: int, data: EtapaUpdate, db: Session = Depends(get_db)):
    etapa = db.query(Etapa).filter(Etapa.id == etapa_id).first()
    if not etapa:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")

    if data.fase_id is not None and data.fase_id != etapa.fase_id:
        fase_exists = db.query(Fase).filter(Fase.id == data.fase_id).first()
        if not fase_exists:
            raise HTTPException(status_code=400, detail="Fase indicada no existe")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(etapa, key, value)

    db.commit()
    db.refresh(etapa)
    return etapa

# -------------------- DELETE --------------------
@router.delete("/{etapa_id}")
def delete_etapa(etapa_id: int, db: Session = Depends(get_db)):
    etapa = db.query(Etapa).filter(Etapa.id == etapa_id).first()
    if not etapa:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    db.delete(etapa)
    db.commit()
    return {"ok": True}
