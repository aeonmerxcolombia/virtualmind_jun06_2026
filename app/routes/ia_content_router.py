from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.module import Module
from app.models.study_plan import StudyPlan

router = APIRouter(
    prefix="/ia-content",
    tags=["Contenido IA"]
)

class GuardarContenidoIA(BaseModel):
    entidad_tipo: str
    entidad_id: int
    nombre: str
    contenido: str

@router.post("/")
def guardar_contenido_ia(data: GuardarContenidoIA, db: Session = Depends(get_db)):
    if data.entidad_tipo == "modulo":
        modulo = db.query(Module).filter(Module.id == data.entidad_id).first()
        if not modulo:
            raise HTTPException(status_code=404, detail="Módulo no encontrado")
        
        nuevo_modulo = Module(
            study_plan_id=data.entidad_id,
            nombre_del_modulo=data.nombre,
            contenido_generado=data.contenido
        )
        db.add(nuevo_modulo)
        db.commit()
        db.refresh(nuevo_modulo)
        return {"mensaje": "Contenido guardado como nuevo módulo", "id": nuevo_modulo.id, "tipo": "modulo"}
    
    elif data.entidad_tipo == "study_plan":
        plan = db.query(StudyPlan).filter(StudyPlan.id == data.entidad_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan de Estudio no encontrado")
        
        nuevo_modulo = Module(
            study_plan_id=data.entidad_id,
            nombre_del_modulo=data.nombre,
            contenido_generado=data.contenido
        )
        db.add(nuevo_modulo)
        db.commit()
        db.refresh(nuevo_modulo)
        return {"mensaje": "Contenido guardado como nuevo módulo en el plan", "id": nuevo_modulo.id, "tipo": "modulo"}
    
    else:
        raise HTTPException(status_code=400, detail="Tipo de entidad no válido")
