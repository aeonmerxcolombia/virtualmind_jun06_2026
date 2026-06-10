from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.module import Module
from app.schemas.module_schema import ModuleCreate, ModuleUpdate, ModuleOut
from typing import List

router = APIRouter(
    prefix="/modules",
    tags=["Módulos"]
)

@router.post("/", response_model=ModuleOut)
def create_module(module: ModuleCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo módulo en la base de datos con todos los campos del formulario.
    """
    # El método model_dump() de Pydantic convierte el objeto a un diccionario.
    # El `from_attributes = True` en el esquema maneja la conversión de SQLAlchemy a Pydantic.
    db_module = Module(**module.model_dump())
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module

@router.get("/studyplan/{study_plan_id}", response_model=List[ModuleOut])
def get_modules_by_study_plan(study_plan_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todos los módulos de un plan de formación específico.
    """
    modules = db.query(Module).filter(Module.study_plan_id == study_plan_id).all()
    if not modules:
        raise HTTPException(status_code=404, detail="No se encontraron módulos para este plan de formación")
    return modules

@router.get("/{module_id}", response_model=ModuleOut)
def get_module(module_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un módulo por su ID.
    """
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    return module

@router.put("/{module_id}", response_model=ModuleOut)
def update_module(module_id: int, module_update: ModuleUpdate, db: Session = Depends(get_db)):
    """
    Actualiza un módulo por su ID.
    """
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    # Convierte el Pydantic a un diccionario, excluyendo los valores que no se proporcionaron.
    update_data = module_update.dict(exclude_unset=True)
    
    # Actualiza los atributos del objeto de la base de datos
    for key, value in update_data.items():
        setattr(module, key, value)
        
    db.commit()
    db.refresh(module)
    return module

@router.delete("/{module_id}", status_code=204)
def delete_module(module_id: int, db: Session = Depends(get_db)):
    """
    Elimina un módulo por su ID.
    """
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
        
    db.delete(module)
    db.commit()
    return {"message": "Módulo eliminado exitosamente"}

@router.get("/", response_model=List[ModuleOut])
def list_modules(db: Session = Depends(get_db)):
    """
    Lista todos los módulos.
    """
    modules = db.query(Module).all()
    return modules
