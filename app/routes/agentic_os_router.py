from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database.db import get_db
from app.models.agente_rol import AgenteRol
from app.services.agent_executor import executor, AGENT_CATEGORIES
from app.services.hive_orchestrator import hive
import asyncio
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter(prefix="/agentic-os", tags=["agentic-os"])


class ExecuteRequest(BaseModel):
    agent: str
    task: str
    work_dir: Optional[str] = None
    prioridad: str = "medium"
    notas: Optional[str] = None
    source: Optional[str] = "api"


class ExecuteResponse(BaseModel):
    status: str
    agente_id: int
    agent: str
    category: str
    message: str


@router.get("/agentes")
def listar_agentes():
    categories = {}
    for agent_name, category in AGENT_CATEGORIES.items():
        cat_name = {"tradicional": "Tradicionales", "interfaz": "Interfaz", "sistema": "Sistema"}.get(category, category)
        if cat_name not in categories:
            categories[cat_name] = []
        categories[cat_name].append(agent_name)
    return {"total": len(AGENT_CATEGORIES), "categories": categories}


@router.post("/execute", response_model=ExecuteResponse)
def execute_agent(
    req: ExecuteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    category = executor.get_category(req.agent)
    if category == "unknown":
        raise HTTPException(400, f"Agente desconocido: {req.agent}. Usa GET /agentic-os/agentes para ver la lista.")

    db_agente = AgenteRol(
        rol=req.agent,
        descripcion=req.task,
        prioridad=req.prioridad,
        notas=req.notas or f"Ejecutado via /agentic-os/execute | categoria: {category}",
    )
    db.add(db_agente)
    db.commit()
    db.refresh(db_agente)

    work_dir = req.work_dir or executor.get_work_dir(req.agent)

    background_tasks.add_task(_run_and_update, db_agente.id, req.agent, req.task, work_dir, category, req.source)

    return ExecuteResponse(
        status="dispatched",
        agente_id=db_agente.id,
        agent=req.agent,
        category=category,
        message=f"Tarea {db_agente.id} despachada al agente {req.agent}. Evento emitido en la colmena.",
    )


@router.post("/disparar/{agente_id}")
def disparar_agente(background_tasks: BackgroundTasks, agente_id: int, db: Session = Depends(get_db)):
    agente = db.query(AgenteRol).filter(AgenteRol.id == agente_id).first()
    if not agente:
        raise HTTPException(404, "Tarea no encontrada")
    if agente.estado == "completed":
        raise HTTPException(400, "Ya completada")

    agente.estado = "in_progress"
    db.commit()

    category = executor.get_category(agente.rol)
    work_dir = executor.get_work_dir(agente.rol)

    background_tasks.add_task(_run_and_update, agente.id, agente.rol, agente.descripcion, work_dir, category, "api_retrigger")

    return {"status": "dispatched", "agente_id": agente.id, "agent": agente.rol}


@router.post("/cross-task")
def cross_agent_task(
    source_agent: str,
    target_agent: str,
    task_description: str,
    prioridad: str = "medium",
    notas: str = None,
):
    category = executor.get_category(target_agent)
    if category == "unknown":
        raise HTTPException(400, f"Agente destino desconocido: {target_agent}")

    try:
        loop = asyncio.new_event_loop()
        task_id = loop.run_until_complete(
            hive.create_cross_agent_task(source_agent, target_agent, task_description, prioridad, notas)
        )
        loop.close()
        if task_id:
            return {"status": "created", "task_id": task_id, "source": source_agent, "target": target_agent}
        return {"status": "error", "message": "No se pudo crear la tarea"}
    except Exception as e:
        raise HTTPException(500, f"Error creando tarea cruzada: {e}")


@router.get("/events")
def list_hive_events(limit: int = 50):
    import sqlite3
    try:
        conn = sqlite3.connect("/tmp/agentic_os_hive.db")
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM hive_events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"error": str(e)}


@router.get("/tasks")
def list_hive_tasks(limit: int = 50):
    import sqlite3
    try:
        conn = sqlite3.connect("/tmp/agentic_os_hive.db")
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM hive_agent_tasks ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"error": str(e)}


def _run_and_update(agente_id: int, agent_name: str, task: str, work_dir: str, category: str, source: str = "api"):
    result = executor.execute(
        agent_name=agent_name,
        task_description=task,
        task_id=agente_id,
        work_dir=work_dir,
        log_prefix="agentic_os",
    )

    try:
        status = "completed" if result["status"] == "completed" else "failed"
        resultado = f"stdout: {result.get('stdout', '')[:3000]}\nstderr: {result.get('stderr', '')[:1000]}"
        requests.put(
            f"https://localhost:8000/agentes-rol/{agente_id}",
            json={"estado": status, "resultado": resultado[:2000]},
            verify=False,
            timeout=10,
        )
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                hive.emit_event(
                    f"task_{status}",
                    source_agent=agent_name,
                    target_agent=agent_name,
                    task_id=agente_id,
                    outcome=status,
                    payload=resultado[:500],
                )
            )
            loop.close()
        except Exception as ev:
            print(f"[agentic-os] Event emission error: {ev}")
    except Exception as e:
        print(f"[agentic-os] Error updating task {agente_id}: {e}")
