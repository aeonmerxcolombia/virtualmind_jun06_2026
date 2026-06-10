from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.proyecto_participante import ProyectoParticipante
from app.models.user import User
from app.schemas.proyecto_participante_schema import ProyectoParticipanteCreate, ProyectoParticipanteRead
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/participantes", tags=["participantes"])

class ParticipanteConUsuario(BaseModel):
    user_uid: str
    nombre: str
    email: str
    role_id: int

@router.get("/{project_id}/con-usuarios", response_model=List[ParticipanteConUsuario])
def listar_participantes_con_usuarios(project_id: int, db: Session = Depends(get_db)):
    participantes = db.query(ProyectoParticipante).filter(ProyectoParticipante.project_id == project_id).all()
    result = []
    for p in participantes:
        user = db.query(User).filter(User.uid == p.user_uid).first()
        result.append(ParticipanteConUsuario(
            user_uid=p.user_uid,
            nombre=user.nombre if user else "Desconocido",
            email=user.email if user else "",
            role_id=p.role_id
        ))
    return result

@router.post("/", response_model=ProyectoParticipanteRead)
def agregar_participante(data: ProyectoParticipanteCreate, db: Session = Depends(get_db)):
    # Verificar si ya existe
    existente = db.query(ProyectoParticipante).filter(
        ProyectoParticipante.project_id == data.project_id,
        ProyectoParticipante.user_uid == data.user_uid
    ).first()
    
    if existente:
        raise HTTPException(status_code=400, detail="El usuario ya es participante de este proyecto.")
    
    nuevo = ProyectoParticipante(**data.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.get("/counts")
def contar_participantes_por_proyecto(db: Session = Depends(get_db)):
    from sqlalchemy import func
    resultados = db.query(
        ProyectoParticipante.project_id,
        func.count(ProyectoParticipante.id)
    ).group_by(ProyectoParticipante.project_id).all()
    return {str(r[0]): r[1] for r in resultados}

@router.get("/{project_id}", response_model=List[ProyectoParticipanteRead])
def listar_participantes(project_id: int, db: Session = Depends(get_db)):
    return db.query(ProyectoParticipante).filter(ProyectoParticipante.project_id == project_id).all()

@router.delete("/{project_id}/{user_uid}")
def eliminar_participante(project_id: int, user_uid: str, db: Session = Depends(get_db)):
    p = db.query(ProyectoParticipante).filter(
        ProyectoParticipante.project_id == project_id,
        ProyectoParticipante.user_uid == user_uid
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Participante no encontrado")
    
    db.delete(p)
    db.commit()
    return {"message": "Participante eliminado"}
