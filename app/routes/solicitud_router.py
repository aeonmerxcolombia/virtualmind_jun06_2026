# app/routes/solicitud_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from app.database.db import get_db
from app.models.solicitud import SolicitudPieza
from app.schemas.solicitud_schema import SolicitudPiezaCreate, SolicitudPiezaOut

router = APIRouter(
    prefix="/solicitudes",
    tags=["Solicitudes"]
)

@router.post(
    "/",
    response_model=SolicitudPiezaOut,
    status_code=status.HTTP_201_CREATED
)
def crear_solicitud(
    data: SolicitudPiezaCreate,
    db: Session = Depends(get_db)
):
    nueva = SolicitudPieza(**data.model_dump())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.get(
    "/",
    response_model=list[SolicitudPiezaOut]
)
def listar_solicitudes(db: Session = Depends(get_db)):
    return db.query(SolicitudPieza).all()

@router.get(
    "/{sol_id}",
    response_model=SolicitudPiezaOut
)
def obtener_solicitud(sol_id: int, db: Session = Depends(get_db)):
    sol = db.query(SolicitudPieza).filter(SolicitudPieza.id == sol_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return sol

@router.put(
    "/{sol_id}/aceptar",
    response_model=SolicitudPiezaOut
)
def aceptar_solicitud(
    sol_id: int,
    fecha_entrega: date,
    db: Session = Depends(get_db)
):
    sol = db.query(SolicitudPieza).filter(SolicitudPieza.id == sol_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    sol.fecha_entrega = fecha_entrega
    db.commit()
    db.refresh(sol)
    return sol

@router.delete(
    "/{sol_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_solicitud(sol_id: int, db: Session = Depends(get_db)):
    sol = db.query(SolicitudPieza).filter(SolicitudPieza.id == sol_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    db.delete(sol)
    db.commit()

