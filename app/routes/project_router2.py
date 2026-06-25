import json
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.db import get_db
from app.models.project import Project
from app.models.fase import Fase
from app.schemas.project_schema import ProjectRead, ProjectCreate
from app.services.log_service import registrar_log, notificar_proyecto_creado
from app.services.email_service import notify_project_created
from app.auth.jwt_handler import verify_token

router = APIRouter(prefix="/projects", tags=["projects"])


def get_token(usuario_token: Optional[str] = Header(None)):
    return usuario_token


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db)
):
    proyecto_data = project_in.model_dump()
    
    # Campos válidos del modelo Project
    valid_fields = {
        'name', 'client_id', 'codigo_referencia', 'start_date', 'end_date',
        'tipo_proyecto', 'tipo_proyecto_personalizado', 'estado', 'description',
        'fase_id', 'lenguaje_incluyente', 'lenguaje_inclusivo_tipo', 'lenguaje_inclusivo_otro',
        'inclusion_digital', 'inclusion_digital_web', 'inclusion_digital_asistiva',
        'inclusion_digital_universal', 'inclusion_digital_educativa', 'inclusion_digital_otro',
        'idioma', 'idioma_otro',
        'tipografia_titulo_fuente', 'tipografia_titulo_tamano', 'tipografia_titulo_negrita', 'tipografia_titulo_cursiva',
        'tipografia_subtitulo_fuente', 'tipografia_subtitulo_tamano', 'tipografia_subtitulo_negrita', 'tipografia_subtitulo_cursiva',
        'tipografia_parrafo_fuente', 'tipografia_parrafo_tamano', 'tipografia_parrafo_negrita', 'tipografia_parrafo_cursiva',
        'horas_curso', 'diseno_grafico_tipo', 'diseno_grafico_paleta',
        'cesion_derechos', 'derechos_patrimoniales_autor', 'acuerdo_confidencialidad',
        'entrega_fuentes', 'entrega_escrito_autor', 'entrega_diseno_instruccional',
        'publico_objetivo', 'publico_objetivo_otro',
        'horas_aprendizaje_autonomo_virtual', 'horas_actividades_aprendizaje',
        'observaciones', 'etapa'
    }
    
    # Filtrar solo campos válidos
    filtered_data = {}
    for key, value in proyecto_data.items():
        if key in valid_fields:
            # Convertir listas a JSON string
            if isinstance(value, list):
                filtered_data[key] = json.dumps(value)
            elif value is None or value == '':
                filtered_data[key] = None
            else:
                filtered_data[key] = value

    # Validar fase_id
    if filtered_data.get("fase_id") is not None and filtered_data["fase_id"] > 0:
        fase = db.query(Fase).filter(Fase.id == filtered_data["fase_id"]).first()
        if not fase:
            raise HTTPException(status_code=400, detail="La fase especificada no existe")
    else:
        filtered_data["fase_id"] = None

    db_project = Project(**filtered_data)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    if db_project.publico_objetivo:
        try:
            db_project.publico_objetivo = json.loads(db_project.publico_objetivo)
        except Exception:
            db_project.publico_objetivo = []

    # Log deshabilitado para prueba
    # user_id = token_data.get("user_id") if token_data else None
    # if user_id:
    #     registrar_log(db=db, usuario_id=str(user_id), tipo_evento="proyecto_creado", descripcion=f"Proyecto '{db_project.name}' creado")
    # from app.models.user import User
    # cliente = db.query(User).filter(User.uid == db_project.client_id).first()
    # cliente_nombre = cliente.nombre if cliente else "Cliente"
    # notificar_proyecto_creado(db, db_project.name, cliente_nombre, str(user_id) if user_id else "")
    # await notify_project_created(db, db_project.name, db_project.client_id)

    return db_project

@router.get("/", response_model=List[ProjectRead])
def list_projects(
    estado: Optional[str] = Query(None),
    fase_id: Optional[int] = Query(None),
    rol_vista: Optional[str] = Query(None),  # NUEVO: Define desde qué vista se hace la petición
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    query = db.query(Project)

    if authorization:
        try:
            # Extraer token del header Authorization
            token = authorization.replace("Bearer ", "")
            from app.auth.jwt_handler import SECRET_KEY, ALGORITHM
            import jwt
            token_data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_uid = token_data.get("sub")

            if user_uid:
                from app.models.user import User
                from app.models.tarea import Tarea
                user = db.query(User).filter(User.uid == user_uid).first()
                
                if user:
                    user_roles = [role.name for role in user.roles]
                    
                    # LÓGICA CORREGIDA: Si está en la vista de autor, O NO es superadmin
                    # forzamos a que solo vea los proyectos donde tiene tareas.
                    if rol_vista == 'autor' or 'superadmin' not in user_roles:
                        tareas_asignadas = db.query(Tarea.project_id).filter(Tarea.asignado == user_uid).distinct().all()

                        if tareas_asignadas:
                            # Tiene tareas asignadas, filtrar por esos proyectos
                            proyectos_ids = [p[0] for p in tareas_asignadas]
                            query = query.filter(Project.id.in_(proyectos_ids))
                        else:
                            # Si es autor (o rol restrictivo) y no tiene tareas, bloqueamos la consulta
                            # Devolviendo un filtro imposible para que retorne una lista vacía
                            query = query.filter(Project.id == -1) 

        except Exception as e:
            # VULNERABILIDAD CORREGIDA: Fallo cerrado. Si el token es inválido, rechazamos la petición.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token inválido, expirado o corrupto."
            )
    else:
        # Si no hay token, no se devuelve nada por seguridad
        query = query.filter(Project.id == -1)

    # Filtros adicionales
    if estado:
        query = query.filter(Project.estado == estado)
    if fase_id:
        query = query.filter(Project.fase_id == fase_id)

    projects = query.order_by(Project.id.desc()).all()
    for p in projects:
        if p.publico_objetivo:
            try:
                p.publico_objetivo = json.loads(p.publico_objetivo)
            except Exception:
                p.publico_objetivo = []
                
    return projects

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if project.publico_objetivo:
        try:
            project.publico_objetivo = json.loads(project.publico_objetivo)
        except Exception:
            project.publico_objetivo = []
    return project


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    updated: ProjectCreate,
    db: Session = Depends(get_db),
    token: str = Depends(get_token)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    updated_data = updated.dict(exclude_unset=True)

    if "fase_id" in updated_data and updated_data["fase_id"] is not None:
        fase = db.query(Fase).filter(Fase.id == updated_data["fase_id"]).first()
        if not fase:
            raise HTTPException(status_code=400, detail="La fase especificada no existe")

    if "publico_objetivo" in updated_data and updated_data["publico_objetivo"] is not None:
        updated_data["publico_objetivo"] = json.dumps(updated_data["publico_objetivo"])

    for key, value in updated_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)

    if project.publico_objetivo:
        try:
            project.publico_objetivo = json.loads(project.publico_objetivo)
        except Exception:
            project.publico_objetivo = []

    # Registrar log
    if token:
        registrar_log(
            db=db,
            usuario_id=token,
            tipo_evento="proyecto_actualizado",
            descripcion=f"Proyecto '{project.name}' actualizado"
        )

    return project


@router.patch("/{project_id}/estado", response_model=ProjectRead)
def cambiar_estado_proyecto(
    project_id: int,
    nuevo_estado: str,
    db: Session = Depends(get_db),
    token: str = Depends(get_token)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project.estado = nuevo_estado
    db.commit()
    db.refresh(project)

    if project.publico_objetivo:
        try:
            project.publico_objetivo = json.loads(project.publico_objetivo)
        except Exception:
            project.publico_objetivo = []

    # Registrar log
    if token:
        registrar_log(
            db=db,
            usuario_id=token,
            tipo_evento="proyecto_estado_cambiado",
            descripcion=f"Proyecto '{project.name}' cambió estado a '{nuevo_estado}'"
        )

    return project


@router.patch("/{project_id}/fase", response_model=ProjectRead)
def cambiar_fase_proyecto(
    project_id: int,
    nueva_fase_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(get_token)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    fase = db.query(Fase).filter(Fase.id == nueva_fase_id).first()
    if not fase:
        raise HTTPException(status_code=400, detail="La fase especificada no existe")

    project.fase_id = nueva_fase_id
    db.commit()
    db.refresh(project)

    if project.publico_objetivo:
        try:
            project.publico_objetivo = json.loads(project.publico_objetivo)
        except Exception:
            project.publico_objetivo = []

    # Registrar log
    if token:
        registrar_log(
            db=db,
            usuario_id=token,
            tipo_evento="proyecto_fase_cambiada",
            descripcion=f"Proyecto '{project.name}' cambió a fase '{nueva_fase_id}'"
        )

    return project

