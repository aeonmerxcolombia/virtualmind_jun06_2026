from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.tarea_ia import TareaIA
from app.services.agent_executor import executor
from app.services.hive_orchestrator import hive
import asyncio
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter(prefix="/orquestador-ia", tags=["orquestador-ia"])

URL_API_LOCAL = "https://localhost:8000/tareas-ia"

RUTAS_PROYECTO = {
    "backend": "/home/ubuntu/backend",
    "frontend": "/var/www/html",
    "server": "/etc",
    "database": "/home/ubuntu/backend",
    "docs": "/home/william/docs",
    "qa": "/home/ubuntu/backend"
}


def ejecutar_agente_en_segundo_plano(tarea_id: int, directorio_trabajo: str, instrucciones_texto: str, agente: str = "backend"):
    logfile = f"/tmp/opencode_tarea_{tarea_id}.log"

    def log(msg):
        with open(logfile, "a") as f:
            f.write(f"{msg}\n")
        print(msg, flush=True)

    log(f"[*] [Tarea {tarea_id}] Agente: {agente} | Directorio: {directorio_trabajo}")

    result = executor.execute(
        agent_name=agente,
        task_description=instrucciones_texto,
        task_id=tarea_id,
        work_dir=directorio_trabajo,
        timeout=150,
        log_prefix="opencode_tarea",
    )

    log(f"\n===== LOGS ({tarea_id}) =====")
    if result.get("stdout"):
        log(result["stdout"])
    if result.get("stderr"):
        log(f"ERRORES: {result['stderr']}")
    log(f"===========================\n")

    status = "completed" if result["status"] == "completed" else "failed"

    if status == "completed":
        requests.put(f"{URL_API_LOCAL}/{tarea_id}", json={"estado": "completed"}, verify=False, timeout=10)
        log(f"[+] Tarea {tarea_id} completada.")
    else:
        log(f"[!] Tarea {tarea_id} fallo")
        requests.put(f"{URL_API_LOCAL}/{tarea_id}", json={"estado": "failed"}, verify=False)

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            hive.emit_event(
                f"task_{status}",
                source_agent=agente,
                target_agent=agente,
                task_id=tarea_id,
                outcome=status,
                payload=f"Orquestador IA tarea {tarea_id}",
            )
        )
        loop.close()
    except Exception:
        pass


@router.post("/disparar")
def trigger_orquestador(background_tasks: BackgroundTasks, tarea_id: int = None, db: Session = Depends(get_db)):
    if tarea_id:
        tarea = db.query(TareaIA).filter(TareaIA.id == tarea_id).first()
        if not tarea:
            return {"status": "error", "message": "Tarea no encontrada"}
        if tarea.estado == "completed":
            return {"status": "error", "message": "La tarea ya está completada"}
    else:
        tarea = db.query(TareaIA).filter(TareaIA.estado == "pending").order_by(TareaIA.id.desc()).first()
        if not tarea:
            return {"status": "idle", "message": "No hay tareas pendientes."}

    cwd_objetivo = RUTAS_PROYECTO.get(tarea.responsable, "/home/ubuntu/backend")

    if background_tasks:
        background_tasks.add_task(
            ejecutar_agente_en_segundo_plano,
            tarea.id,
            cwd_objetivo,
            f"{tarea.descripcion}. Notas: {tarea.notas}",
            tarea.responsable
        )
        return {"status": "dispatched", "tarea_id": tarea.id}
    else:
        return {"status": "error", "message": "BackgroundTasks no disponible"}
