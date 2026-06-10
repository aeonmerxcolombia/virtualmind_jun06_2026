from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.database.db import get_db
from app.models.tarea import Tarea
from app.models.project import Project
from app.schemas.tarea_schema import TareaOut
from app.services.email_service import notify_task_created
from app.services.log_service import notificar_tarea_creada
from app.models.user import User
from app.auth.jwt_handler import verify_token

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

router = APIRouter(prefix="/tareas", tags=["tareas"])

# ------------------ CREAR ------------------
@router.post("/", response_model=TareaOut)
async def create_tarea(
    titulo: str = Form(...),
    descripcion: Optional[str] = Form(None),
    fecha_inicio: Optional[str] = Form(None),
    fecha_entrega: Optional[str] = Form(None),
    estado: Optional[str] = Form(None),
    prioridad: Optional[str] = Form(None),
    asignado: Optional[str] = Form(None),
    seguidores: List[str] = Form([]),  # ✅ lista directa
    fase_id: Optional[int] = Form(None),
    etapa_id: Optional[int] = Form(None),
    project_id: int = Form(...),
    adjuntos: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    roles_crear = ["superadmin", "admin", "cliente", "coordinador"]
    user_roles = token_data.get("roles", [])
    if not any(r in user_roles for r in roles_crear):
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para crear tareas. Solo admin, superadmin, cliente o coordinador."
        )
    adjuntos_urls = []
    if adjuntos:
        for file in adjuntos:
            file_location = os.path.join(UPLOAD_FOLDER, file.filename)
            with open(file_location, "wb") as f:
                f.write(await file.read())
            adjuntos_urls.append(f"/static/uploads/{file.filename}")

    tarea = Tarea(
        titulo=titulo,
        descripcion=descripcion,
        fecha_inicio=fecha_inicio,
        fecha_entrega=fecha_entrega,
        estado=estado or "Pendiente",
        prioridad=prioridad,
        asignado=asignado,
        fase_id=fase_id or 1,
        etapa_id=etapa_id or 1,
        project_id=project_id,
        creado_por=token_data.get("user_id")
    )
    tarea.seguidores_list = seguidores
    tarea.adjuntos_list = adjuntos_urls

    db.add(tarea)
    db.commit()
    db.refresh(tarea)

    project = db.query(Project).filter(Project.id == project_id).first()
    project_name = project.name if project else "Sin proyecto"
    
    await notify_task_created(
        db=db,
        task_title=tarea.titulo,
        project_name=project_name,
        asignado=tarea.asignado,
        seguidores=tarea.seguidores_list
    )

    user_id = token_data.get("user_id") if token_data else None
    if user_id:
        asignado_nombre = tarea.asignado or "Sin asignar"
        notificar_tarea_creada(db, tarea.titulo, project_name, asignado_nombre, str(user_id))

    tarea.seguidores = tarea.seguidores_list
    tarea.adjuntos = tarea.adjuntos_list

    return tarea

# ------------------ LISTAR ------------------
@router.get("/", response_model=List[TareaOut])
def list_tareas(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    user_id = token_data.get("user_id")
    roles = token_data.get("roles", [])
    
    # Roles que pueden crear/gestionar tareas: ven todas las que han creado
    roles_con_creacion = ["superadmin", "admin", "autor", "disenador-instruccional", 
                          "corrector-de-estilo", "editor", "coordinador", "gerente general",
                          "ingeniero-lms", "revisor-qa", "disenador-grafico", "desarrollador-multimedia",
                          "video", "animador-3d", "animador-2d", "guionista"]
    
    # Superadmin y admin ven todas las tareas
    if user_id and ("superadmin" in roles or "admin" in roles):
        tareas = db.query(Tarea).all()
    # Roles con permiso de creación ven todas las tareas que han creado
    elif user_id and any(r in roles for r in roles_con_creacion):
        tareas = db.query(Tarea).filter(Tarea.creado_por == user_id).all()
    # Otros roles: solo tareas donde están asignados
    elif user_id:
        from sqlalchemy import or_
        tareas = db.query(Tarea).filter(
            or_(Tarea.creado_por == user_id, Tarea.asignado.contains(str(user_id)))
        ).all()
    else:
        tareas = []
    
    for t in tareas:
        t.seguidores = t.seguidores_list
        t.adjuntos = t.adjuntos_list
        if t.asignado and (len(t.asignado) > 30 or '-' in t.asignado):
            user = db.query(User).filter(
                (User.uid == t.asignado) | (User.email == t.asignado)
            ).first()
            if user:
                t.asignado = user.nombre
    return tareas

# ------------------ OBTENER ------------------
@router.get("/{tarea_id}", response_model=TareaOut)
def get_tarea(tarea_id: int, db: Session = Depends(get_db)):
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    tarea.seguidores = tarea.seguidores_list
    tarea.adjuntos = tarea.adjuntos_list
    if tarea.asignado and (len(tarea.asignado) > 30 or '-' in tarea.asignado):
        user = db.query(User).filter(
            (User.uid == tarea.asignado) | (User.email == tarea.asignado)
        ).first()
        if user:
            tarea.asignado = user.nombre
    return tarea

# ------------------ ACTUALIZAR ------------------
@router.put("/{tarea_id}", response_model=TareaOut)
async def update_tarea(
    tarea_id: int,
    titulo: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    fecha_inicio: Optional[str] = Form(None),
    fecha_entrega: Optional[str] = Form(None),
    estado: Optional[str] = Form(None),
    prioridad: Optional[str] = Form(None),
    asignado: Optional[str] = Form(None),
    seguidores: Optional[List[str]] = Form(None),  # ✅ lista opcional
    fase_id: Optional[int] = Form(None),
    etapa_id: Optional[int] = Form(None),
    project_id: Optional[int] = Form(None),
    adjuntos: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db)
):
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    if titulo is not None: tarea.titulo = titulo
    if descripcion is not None: tarea.descripcion = descripcion
    if fecha_inicio is not None: tarea.fecha_inicio = fecha_inicio
    if fecha_entrega is not None: tarea.fecha_entrega = fecha_entrega
    if estado is not None: tarea.estado = estado
    if prioridad is not None: tarea.prioridad = prioridad
    if asignado is not None: tarea.asignado = asignado
    if fase_id is not None: tarea.fase_id = fase_id
    if etapa_id is not None: tarea.etapa_id = etapa_id
    if project_id is not None: tarea.project_id = project_id
    if seguidores is not None: tarea.seguidores_list = seguidores  # ✅ directo

    if adjuntos:
        adjuntos_urls = []
        for file in adjuntos:
            file_location = os.path.join(UPLOAD_FOLDER, file.filename)
            with open(file_location, "wb") as f:
                f.write(await file.read())
            adjuntos_urls.append(f"/static/uploads/{file.filename}")
        tarea.adjuntos_list = adjuntos_urls

    db.commit()
    db.refresh(tarea)
    tarea.seguidores = tarea.seguidores_list
    tarea.adjuntos = tarea.adjuntos_list
    return tarea

# ------------------ ELIMINAR ------------------
@router.delete("/{tarea_id}")
def delete_tarea(tarea_id: int, db: Session = Depends(get_db)):
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    db.delete(tarea)
    db.commit()
    return {"ok": True}
