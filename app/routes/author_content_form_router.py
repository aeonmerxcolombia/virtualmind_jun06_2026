# app/routes/author_content_form_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database.db import get_db
from app.models.author_content_form import AuthorContentForm
from app.schemas.author_content_form_schema import (
    AuthorContentFormCreate, AuthorContentFormUpdate, AuthorContentFormOut
)

router = APIRouter(prefix="/author_content_forms", tags=["Autor de Contenidos"])

@router.post("/", response_model=AuthorContentFormOut)
def create_author_form(payload: AuthorContentFormCreate, db: Session = Depends(get_db)):
    obj = AuthorContentForm(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=List[AuthorContentFormOut])
def list_author_forms(project_id: int | None = Query(None), db: Session = Depends(get_db)):
    q = db.query(AuthorContentForm)
    if project_id is not None:
        q = q.filter(AuthorContentForm.project_id == project_id)
    return q.order_by(AuthorContentForm.created_at.desc()).all()

@router.get("/{form_id}", response_model=AuthorContentFormOut)
def get_author_form(form_id: int, db: Session = Depends(get_db)):
    obj = db.query(AuthorContentForm).filter(AuthorContentForm.id == form_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Formulario de autor no encontrado")
    return obj

@router.put("/{form_id}", response_model=AuthorContentFormOut)
def update_author_form(form_id: int, upd: AuthorContentFormUpdate, db: Session = Depends(get_db)):
    obj = db.query(AuthorContentForm).filter(AuthorContentForm.id == form_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Formulario de autor no encontrado")
    for k, v in upd.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{form_id}")
def delete_author_form(form_id: int, db: Session = Depends(get_db)):
    obj = db.query(AuthorContentForm).filter(AuthorContentForm.id == form_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Formulario de autor no encontrado")
    db.delete(obj)
    db.commit()
    return {"ok": True}

