from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.study_plan import StudyPlan
from app.schemas.study_plan_schema import StudyPlanCreate, StudyPlanUpdate, StudyPlanOut
from app.models.module import Module
from app.schemas.module_schema import ModuleOut
from app.services.log_service import notificar_plan_estudio_creado
from app.services.email_service import notify_study_plan_created
from app.auth.jwt_handler import verify_token
from app.models.project import Project

router = APIRouter(
    prefix="/study_plans",
    tags=["Planes de Estudio"]
)


@router.post("/", response_model=StudyPlanOut)
async def create_study_plan(
    plan: StudyPlanCreate, 
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    db_plan = StudyPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    user_id = token_data.get("user_id") if token_data else None
    
    project = db.query(Project).filter(Project.id == db_plan.project_id).first()
    proyecto_nombre = project.name if project else "Sin proyecto"
    
    if user_id:
        notificar_plan_estudio_creado(db, db_plan.name, proyecto_nombre, str(user_id))
        await notify_study_plan_created(db, db_plan.name, proyecto_nombre, str(user_id))

    return db_plan

@router.get("/project/{project_id}", response_model=list[StudyPlanOut])
def get_study_plans_by_project(project_id: int, db: Session = Depends(get_db)):
    plans = db.query(StudyPlan).filter(StudyPlan.project_id == project_id).all()
    
    for plan in plans:
        if hasattr(plan, "objetivos_especificos"):
            if isinstance(plan.objetivos_especificos, str):
                try:
                    import json
                    plan.objetivos_especificos = json.loads(plan.objetivos_especificos)
                except:
                    plan.objetivos_especificos = [plan.objetivos_especificos] if plan.objetivos_especificos else []
    
    return plans

@router.get("/{plan_id}", response_model=StudyPlanOut)
def get_study_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")

    # --- Parchar objetivos_especificos: puede venir como string JSON ---
    if hasattr(plan, "objetivos_especificos"):
        if isinstance(plan.objetivos_especificos, str):
            try:
                import json
                plan.objetivos_especificos = json.loads(plan.objetivos_especificos)
            except:
                plan.objetivos_especificos = [plan.objetivos_especificos] if plan.objetivos_especificos else []

    # --- Parchar módulos: palabras_clave como lista ---
    if hasattr(plan, "modules"):
        for mod in plan.modules:
            if hasattr(mod, "palabras_clave"):
                if isinstance(mod.palabras_clave, str):
                    mod.palabras_clave = [p.strip() for p in mod.palabras_clave.split(",") if p.strip()]
    return plan


import json

@router.put("/{plan_id}", response_model=StudyPlanOut)
def update_study_plan(plan_id: int, plan_update: StudyPlanUpdate, db: Session = Depends(get_db)):
    plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")
    
    update_data = plan_update.dict(exclude_unset=True)
    
    if 'objetivos_especificos' in update_data and isinstance(update_data['objetivos_especificos'], list):
        update_data['objetivos_especificos'] = json.dumps(update_data['objetivos_especificos'])
    
    for k, v in update_data.items():
        setattr(plan, k, v)
    db.commit()
    db.refresh(plan)
    
    # Convertir objetivos_especificos a lista para la respuesta
    if hasattr(plan, "objetivos_especificos"):
        if isinstance(plan.objetivos_especificos, str):
            try:
                plan.objetivos_especificos = json.loads(plan.objetivos_especificos)
            except:
                plan.objetivos_especificos = [plan.objetivos_especificos] if plan.objetivos_especificos else []
    
    return plan

@router.delete("/{plan_id}")
def delete_study_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")
    db.delete(plan)
    db.commit()
    return {"ok": True}

# Opcional: obtener plan de estudio con módulos (incluidos)
@router.get("/{plan_id}/with_modules", response_model=StudyPlanOut)
def get_plan_with_modules(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")
    # Esto usa la relación .modules de SQLAlchemy y StudyPlanOut.modules en schema
    return plan

# NUEVO ENDPOINT: Listar todos los planes de estudio
@router.get("/", response_model=list[StudyPlanOut])
def get_all_study_plans(db: Session = Depends(get_db)):
    plans = db.query(StudyPlan).all()
    
    for plan in plans:
        # --- Parchar objetivos_especificos: puede venir como string JSON ---
        if hasattr(plan, "objetivos_especificos"):
            if isinstance(plan.objetivos_especificos, str):
                try:
                    import json
                    plan.objetivos_especificos = json.loads(plan.objetivos_especificos)
                except:
                    plan.objetivos_especificos = [plan.objetivos_especificos] if plan.objetivos_especificos else []
        
        # --- Parchar módulos: palabras_clave como lista ---
        if hasattr(plan, "modules"):
            for mod in plan.modules:
                if hasattr(mod, "palabras_clave"):
                    if isinstance(mod.palabras_clave, str):
                        if mod.palabras_clave.startswith('[') and mod.palabras_clave.endswith(']'):
                            try:
                                import json
                                mod.palabras_clave = json.loads(mod.palabras_clave)
                            except:
                                mod.palabras_clave = [p.strip() for p in mod.palabras_clave.split(",") if p.strip()]
                        else:
                            mod.palabras_clave = [p.strip() for p in mod.palabras_clave.split(",") if p.strip()]
    
    return plans
