from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.database.db import get_db
from app.models.cronograma import Cronograma
from app.models.project import Project
from app.models.fase import Fase
from app.models.etapa import Etapa
from app.routes.project_router import get_token
from app.services.log_service import crear_notificacion
from app.schemas.cronograma_schema import (
    CronogramaCreate,
    CronogramaRead,
    CronogramaUpdate,
    Fase as CronoFaseSchema,
)
from pydantic import BaseModel

router = APIRouter(prefix="/cronogramas", tags=["Cronogramas"])

class EstadoUpdate(BaseModel):
    estado: str

# -------- Crear un Cronograma --------
@router.post("/", response_model=CronogramaRead, status_code=201)
def create_cronograma(cronograma: CronogramaCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == cronograma.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Proyecto con id {cronograma.project_id} no encontrado")
    
    existing_cronograma = db.query(Cronograma).filter(Cronograma.project_id == cronograma.project_id).first()
    if existing_cronograma:
        raise HTTPException(status_code=409, detail=f"El proyecto {cronograma.project_id} ya tiene un cronograma asociado.")

    if cronograma.estructura and project.start_date and project.end_date:
        for fase in cronograma.estructura:
            if not (project.start_date <= fase.fecha_inicio <= project.end_date and
                    project.start_date <= fase.fecha_fin <= project.end_date):
                raise HTTPException(status_code=400, detail=f"Las fechas de la fase '{fase.nombre_fase}' están fuera del rango del proyecto.")
            
            for etapa in fase.etapas:
                if not (fase.fecha_inicio <= etapa.fecha_inicio <= fase.fecha_fin and
                        fase.fecha_inicio <= etapa.fecha_fin <= fase.fecha_fin):
                    raise HTTPException(status_code=400, detail=f"Las fechas de la etapa '{etapa.nombre_etapa}' están fuera del rango de su fase.")

    # =================================================================
    # CORRECCIÓN: Usar jsonable_encoder para preparar los datos
    # =================================================================
    cronograma_data = jsonable_encoder(cronograma)
    new_cronograma = Cronograma(**cronograma_data)
    
    db.add(new_cronograma)
    db.commit()
    db.refresh(new_cronograma)
    return new_cronograma

# -------- Listar todos los Cronogramas --------  # <--- PÉGALO AQUÍ
@router.get("/", response_model=List[CronogramaRead])
def get_all_cronogramas(db: Session = Depends(get_db)):
    return db.query(Cronograma).all()



# -------- Obtener el cronograma de un proyecto específico --------
@router.get("/project/{project_id}", response_model=CronogramaRead)
def get_cronograma_by_project(project_id: int, db: Session = Depends(get_db)):
    cronograma = db.query(Cronograma).filter(Cronograma.project_id == project_id).first()
    if not cronograma:
        raise HTTPException(status_code=404, detail=f"No se encontró un cronograma para el proyecto {project_id}")
    return cronograma

# -------- Obtener un cronograma por su propio ID --------
@router.get("/{cronograma_id}", response_model=CronogramaRead)
def get_cronograma(cronograma_id: int, db: Session = Depends(get_db)):
    cronograma = db.query(Cronograma).filter(Cronograma.id == cronograma_id).first()
    if not cronograma:
        raise HTTPException(status_code=404, detail="Cronograma no encontrado")
    return cronograma

# -------- Actualizar un cronograma --------
@router.put("/{cronograma_id}", response_model=CronogramaRead)
def update_cronograma(cronograma_id: int, updates: CronogramaUpdate, db: Session = Depends(get_db)):
    cronograma = db.query(Cronograma).filter(Cronograma.id == cronograma_id).first()
    if not cronograma:
        raise HTTPException(status_code=404, detail="Cronograma no encontrado")

    # =================================================================
    # CORRECCIÓN: Usar jsonable_encoder también aquí
    # =================================================================
    update_data = jsonable_encoder(updates, exclude_unset=True)

    if 'estructura' in update_data and cronograma.project.start_date and cronograma.project.end_date:
        project = cronograma.project
        # La validación de la lógica de fechas se puede añadir aquí si se desea para las actualizaciones
        # (similar a como se hace en el endpoint de creación)

    for key, value in update_data.items():
        setattr(cronograma, key, value)

    db.commit()
    db.refresh(cronograma)
    return cronograma

# -------- Actualizar SOLO el estado de un cronograma --------
@router.patch("/{cronograma_id}/estado", response_model=CronogramaRead)
def update_cronograma_estado(cronograma_id: int, estado_update: EstadoUpdate, db: Session = Depends(get_db)):
    cronograma = db.query(Cronograma).filter(Cronograma.id == cronograma_id).first()
    if not cronograma:
        raise HTTPException(status_code=404, detail="Cronograma no encontrado")
    cronograma.estado = estado_update.estado
    db.commit()
    db.refresh(cronograma)
    return cronograma

# -------- Eliminar un cronograma --------
@router.delete("/{cronograma_id}", status_code=204)
def delete_cronograma(cronograma_id: int, db: Session = Depends(get_db)):
    cronograma = db.query(Cronograma).filter(Cronograma.id == cronograma_id).first()
    if not cronograma:
        raise HTTPException(status_code=404, detail="Cronograma no encontrado")
    db.delete(cronograma)
    db.commit()
    return {"message": "Cronograma eliminado"}

# -------- Cerrar un cronograma (marcar como cerrado) --------
@router.patch("/{cronograma_id}/cerrar", response_model=CronogramaRead)
def cerrar_cronograma(cronograma_id: int, db: Session = Depends(get_db), token: str = Depends(get_token)):
    cronograma = db.query(Cronograma).filter(Cronograma.id == cronograma_id).first()
    if not cronograma:
        raise HTTPException(status_code=404, detail="Cronograma no encontrado")
    if cronograma.estado == "cerrado":
        raise HTTPException(status_code=400, detail="El cronograma ya está cerrado")

    # Cerrar fases y etapas en la estructura
    estructura = cronograma.estructura or []
    for fase in estructura:
        fase["estado"] = "cerrada"
        for etapa in fase.get("etapas", []):
            etapa["estado"] = "cerrada"
    cronograma.estructura = estructura
    cronograma.estado = "cerrado"

    project = db.query(Project).filter(Project.id == cronograma.project_id).first()
    if project and project.estado != "Activo":
        project.estado = "Activo"
    db.commit()
    db.refresh(cronograma)
    if project and token:
        crear_notificacion(
            db=db, usuario_id=token,
            tipo_evento="cronograma_cerrado",
            descripcion=f"Cronograma '{cronograma.nombre}' cerrado con {len(estructura)} fases. Proyecto '{project.name}' activado.",
            link=f"/r/superadmin/cronograma/ver-cronograma.html?cronograma_id={cronograma.id}"
        )
    return cronograma

# -------- IA: Sugerir fases y etapas según tipo de proyecto --------
class SugerirCronogramaRequest(BaseModel):
    tipo_proyecto: str
    descripcion: str = ""
    horas_curso: Optional[float] = None

@router.post("/sugerir-ia")
def sugerir_cronograma_ia(
    request: SugerirCronogramaRequest,
    authorization: Optional[str] = Header(None),
):
    if not authorization:
        raise HTTPException(status_code=401, detail="No autorizado")

    token = authorization.replace("Bearer ", "")
    prompt = f"""Eres un experto en gestión de proyectos educativos. Basado en el siguiente proyecto, genera las fases y etapas recomendadas para su cronograma.

Tipo de proyecto: {request.tipo_proyecto}
Descripción: {request.descripcion}
{"Horas totales: " + str(request.horas_curso) if request.horas_curso else ""}

Genera una estructura de cronograma con fases y etapas. Cada fase debe tener un nombre descriptivo y cada etapa debe tener un nombre y descripción.

FORMATO EXACTO (devuelve SOLO JSON válido, sin markdown):
[
  {{
    "nombre_fase": "Nombre de la Fase 1",
    "etapas": [
      {{ "nombre_etapa": "Nombre Etapa 1", "descripcion": "Descripción breve" }},
      {{ "nombre_etapa": "Nombre Etapa 2", "descripcion": "Descripción breve" }}
    ]
  }}
]

Recomendación: Genera entre 3 y 5 fases, cada una con 2-4 etapas.
"""
    try:
        from app.auth.jwt_handler import SECRET_KEY, ALGORITHM
        import jwt
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        import requests
        gemini_url = "https://gestordecursos.pegui.edu.co:8000/chat/gemini"
        response = requests.post(
            gemini_url,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            json={"prompt": prompt},
            timeout=30
        )
        if response.ok:
            data = response.json()
            texto = data.get("respuesta") or data.get("mensaje") or ""
            texto_limpio = texto.strip()
            if texto_limpio.startswith("```"):
                texto_limpio = texto_limpio.split("\n", 1)[-1]
                if "```" in texto_limpio:
                    texto_limpio = texto_limpio.split("```")[0]
            try:
                return json.loads(texto_limpio)
            except json.JSONDecodeError:
                return {"sugerencia": texto_limpio, "raw": True}
        return {"error": "No se pudo obtener sugerencia de la IA"}
    except Exception as e:
        return {"error": str(e)}
