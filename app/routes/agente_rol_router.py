from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database.db import get_db
from app.models.agente_rol import AgenteRol
from app.services.agent_executor import executor
from app.services.hive_orchestrator import hive
import asyncio
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter(prefix="/agentes-rol", tags=["agentes-rol"])


class AgenteRolCreate(BaseModel):
    rol: str
    descripcion: str
    prioridad: str = "medium"
    notas: Optional[str] = None

class AgenteRolUpdate(BaseModel):
    estado: Optional[str] = None
    resultado: Optional[str] = None
    notas: Optional[str] = None

class AgenteRolOut(BaseModel):
    id: int
    rol: str
    descripcion: str
    prioridad: str
    estado: str
    user_email: Optional[str] = None
    resultado: Optional[str] = None
    notas: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AgenteRolOut])
def listar_agentes(db: Session = Depends(get_db)):
    return db.query(AgenteRol).order_by(AgenteRol.id.desc()).all()

@router.get("/rol/{rol}", response_model=List[AgenteRolOut])
def listar_por_rol(rol: str, db: Session = Depends(get_db)):
    return db.query(AgenteRol).filter(AgenteRol.rol == rol).order_by(AgenteRol.id.desc()).all()

@router.post("/", response_model=AgenteRolOut)
def crear_agente(tarea: AgenteRolCreate, db: Session = Depends(get_db)):
    db_agente = AgenteRol(
        rol=tarea.rol,
        descripcion=tarea.descripcion,
        prioridad=tarea.prioridad,
        notas=tarea.notas
    )
    db.add(db_agente)
    db.commit()
    db.refresh(db_agente)
    return db_agente

@router.put("/{agente_id}", response_model=AgenteRolOut)
def actualizar_agente(agente_id: int, data: AgenteRolUpdate, db: Session = Depends(get_db)):
    db_agente = db.query(AgenteRol).filter(AgenteRol.id == agente_id).first()
    if not db_agente:
        raise HTTPException(404, "Agente no encontrado")
    if data.estado is not None:
        db_agente.estado = data.estado
    if data.resultado is not None:
        db_agente.resultado = data.resultado
    if data.notas is not None:
        db_agente.notas = data.notas
    db.commit()
    db.refresh(db_agente)
    return db_agente

@router.delete("/{agente_id}")
def eliminar_agente(agente_id: int, db: Session = Depends(get_db)):
    db_agente = db.query(AgenteRol).filter(AgenteRol.id == agente_id).first()
    if not db_agente:
        raise HTTPException(404, "Agente no encontrado")
    db.delete(db_agente)
    db.commit()
    return {"message": "Agente eliminado"}

@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(AgenteRol).count()
    pending = db.query(AgenteRol).filter(AgenteRol.estado == "pending").count()
    in_progress = db.query(AgenteRol).filter(AgenteRol.estado == "in_progress").count()
    completed = db.query(AgenteRol).filter(AgenteRol.estado == "completed").count()
    return {"total": total, "pending": pending, "in_progress": in_progress, "completed": completed}

@router.post("/disparar/{agente_id}")
def disparar_agente(background_tasks: BackgroundTasks, agente_id: int, db: Session = Depends(get_db)):
    agente = db.query(AgenteRol).filter(AgenteRol.id == agente_id).first()
    if not agente:
        raise HTTPException(404, "Agente no encontrado")
    if agente.estado == "completed":
        raise HTTPException(400, "Ya completado")

    agente.estado = "in_progress"
    db.commit()

    directorio = executor.get_work_dir(agente.rol)

    background_tasks.add_task(ejecutar_agente_rol, agente.id, agente.rol, agente.descripcion, directorio)

    return {"status": "dispatched", "agente_id": agente.id}

def ejecutar_agente_rol(agente_id: int, rol: str, descripcion: str, directorio: str):
    logfile = f"/tmp/opencode_rol_{agente_id}.log"

    def log(msg):
        with open(logfile, "a") as f:
            f.write(f"{msg}\n")
        print(msg, flush=True)

    log(f"[*] Agente Rol {agente_id} - Rol: {rol} iniciando")

    result = executor.execute(
        agent_name=rol,
        task_description=descripcion,
        task_id=agente_id,
        work_dir=directorio,
        timeout=120,
        log_prefix="opencode_rol",
    )

    log(f"\n===== RESULTADO ({agente_id}) =====")
    resultado = ""
    if result.get("stdout"):
        log(result["stdout"])
        resultado = result["stdout"]
    if result.get("stderr"):
        log(f"ERRORES: {result['stderr']}")
    log(f"===========================\n")

    status = "completed" if result["status"] == "completed" else "failed"

    if status == "completed":
        requests.put(f"https://localhost:8000/agentes-rol/{agente_id}",
            json={"estado": "completed", "resultado": resultado[:2000]}, verify=False, timeout=10)
        log(f"[+] Agente Rol {agente_id} completado.")
    else:
        log(f"[!] Agente Rol {agente_id} fallo")
        requests.put(f"https://localhost:8000/agentes-rol/{agente_id}",
            json={"estado": "failed"}, verify=False)

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            hive.emit_event(
                f"task_{status}",
                source_agent=rol,
                target_agent=rol,
                task_id=agente_id,
                outcome=status,
                payload=f"Agente Rol {agente_id} - {rol}",
            )
        )
        loop.close()
    except Exception:
        pass
