# app/routes/instructional_design_form_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database.db import get_db
from app.models.instructional_design_form import InstructionalDesignForm
from app.schemas.instructional_design_form_schema import (
    InstructionalDesignFormCreate, InstructionalDesignFormUpdate, InstructionalDesignFormOut
)

router = APIRouter(prefix="/instructional_design_forms", tags=["Diseño Instruccional (Form)"])

@router.post("/", response_model=InstructionalDesignFormOut)
def create_id_form(payload: InstructionalDesignFormCreate, db: Session = Depends(get_db)):
    obj = InstructionalDesignForm(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=List[InstructionalDesignFormOut])
def list_id_forms(project_id: int | None = Query(None), db: Session = Depends(get_db)):
    q = db.query(InstructionalDesignForm)
    if project_id is not None:
        q = q.filter(InstructionalDesignForm.project_id == project_id)
    return q.order_by(InstructionalDesignForm.created_at.desc()).all()

@router.get("/{form_id}", response_model=InstructionalDesignFormOut)
def get_id_form(form_id: int, db: Session = Depends(get_db)):
    obj = db.query(InstructionalDesignForm).filter(InstructionalDesignForm.id == form_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Formulario de diseño instruccional no encontrado")
    return obj

@router.put("/{form_id}", response_model=InstructionalDesignFormOut)
def update_id_form(form_id: int, upd: InstructionalDesignFormUpdate, db: Session = Depends(get_db)):
    obj = db.query(InstructionalDesignForm).filter(InstructionalDesignForm.id == form_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Formulario de diseño instruccional no encontrado")
    for k, v in upd.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{form_id}")
def delete_id_form(form_id: int, db: Session = Depends(get_db)):
    obj = db.query(InstructionalDesignForm).filter(InstructionalDesignForm.id == form_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Formulario de diseño instruccional no encontrado")
    db.delete(obj)
    db.commit()
    return {"ok": True}

