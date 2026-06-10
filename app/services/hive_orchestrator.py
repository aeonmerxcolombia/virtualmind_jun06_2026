import asyncio
import json
import sqlite3
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.colmena.config import settings

logger = logging.getLogger("hive_orchestrator")

HIVE_DB_PATH = "/tmp/agentic_os_hive.db"


def _init_hive_db():
    os.makedirs(os.path.dirname(HIVE_DB_PATH), exist_ok=True) if os.path.dirname(HIVE_DB_PATH) else None
    with sqlite3.connect(HIVE_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hive_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                source_agent TEXT NOT NULL,
                target_agent TEXT,
                payload TEXT,
                task_id INTEGER,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hive_agent_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_rol_id INTEGER,
                source_agent TEXT NOT NULL,
                target_agent TEXT NOT NULL,
                task_description TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        conn.commit()


def _log_hive_event(event_type: str, source_agent: str, target_agent: str = None,
                    payload: str = None, task_id: int = None, outcome: str = None):
    try:
        with sqlite3.connect(HIVE_DB_PATH) as conn:
            conn.execute(
                "INSERT INTO hive_events (event_type, source_agent, target_agent, payload, task_id, outcome) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (event_type, source_agent, target_agent, payload, task_id, outcome)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging hive event: {e}")


class HiveOrchestrator:
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self._running = False
        self._poll_task = None
        _init_hive_db()

    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

    async def emit_event(self, event_type: str, source_agent: str,
                         target_agent: str = None, payload: str = None,
                         task_id: int = None, outcome: str = None):
        event = {
            "type": event_type,
            "source": source_agent,
            "target": target_agent,
            "payload": payload,
            "task_id": task_id,
            "outcome": outcome,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _log_hive_event(event_type, source_agent, target_agent, payload, task_id, outcome)
        if self.event_bus:
            await self.event_bus.emit_event(event)

    async def create_cross_agent_task(self, source_agent: str, target_agent: str,
                                      task_description: str, prioridad: str = "medium",
                                      notas: str = None) -> Optional[int]:
        from app.database.db import SessionLocal
        from app.models.agente_rol import AgenteRol

        db = SessionLocal()
        try:
            db_agente = AgenteRol(
                rol=target_agent,
                descripcion=task_description,
                prioridad=prioridad,
                notas=notas or f"Creado por {source_agent} via HiveOrchestrator",
            )
            db.add(db_agente)
            db.commit()
            db.refresh(db_agente)

            with sqlite3.connect(HIVE_DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO hive_agent_tasks (agent_rol_id, source_agent, target_agent, task_description) "
                    "VALUES (?, ?, ?, ?)",
                    (db_agente.id, source_agent, target_agent, task_description)
                )
                conn.commit()

            await self.emit_event(
                event_type="task_created",
                source_agent=source_agent,
                target_agent=target_agent,
                task_description=task_description,
                task_id=db_agente.id,
            )

            logger.info(f"[HIVE] {source_agent} -> {target_agent}: tarea {db_agente.id} creada")
            return db_agente.id
        except Exception as e:
            logger.error(f"[HIVE] Error creating cross-agent task: {e}")
            return None
        finally:
            db.close()

    async def mark_task_outcome(self, agent_rol_id: int, outcome: str, result_text: str = None):
        from app.database.db import SessionLocal
        db = SessionLocal()
        try:
            agente = db.query(type('AgenteRol', (), {}))  # placeholder to avoid import issues
            from app.models.agente_rol import AgenteRol as AR
            agente = db.query(AR).filter(AR.id == agent_rol_id).first()
            if agente:
                agente.estado = outcome
                if result_text:
                    agente.resultado = result_text[:2000]
                db.commit()

            with sqlite3.connect(HIVE_DB_PATH) as conn:
                conn.execute(
                    "UPDATE hive_agent_tasks SET status = ?, result = ?, completed_at = CURRENT_TIMESTAMP "
                    "WHERE agent_rol_id = ?",
                    (outcome, result_text, agent_rol_id)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"[HIVE] Error marking task {agent_rol_id}: {e}")
        finally:
            db.close()

    async def poll_pending_system_tasks(self, interval: int = 15):
        from app.database.db import SessionLocal
        from app.models.agente_rol import AgenteRol
        from app.services.agent_executor import executor

        self._running = True
        logger.info(f"[HIVE] Polling loop started (interval={interval}s)")

        while self._running:
            try:
                db = SessionLocal()
                try:
                    pending = (
                        db.query(AgenteRol)
                        .filter(
                            AgenteRol.estado == "pending",
                            AgenteRol.rol.like("sistema_%"),
                        )
                        .order_by(AgenteRol.id.asc())
                        .limit(3)
                        .all()
                    )
                finally:
                    db.close()

                for task in pending:
                    await self._process_system_task(task)

            except Exception as e:
                logger.error(f"[HIVE] Poll error: {e}")

            await asyncio.sleep(interval)

    async def _process_system_task(self, task):
        from app.services.agent_executor import executor

        task_id = task.id
        agent_name = task.rol
        task_desc = task.descripcion

        try:
            db2 = type('SessionLocal', (), {})()
            from app.database.db import SessionLocal
            db2 = SessionLocal()
            try:
                from app.models.agente_rol import AgenteRol
                db_task = db2.query(AgenteRol).filter(AgenteRol.id == task_id).first()
                if db_task:
                    db_task.estado = "in_progress"
                    db2.commit()
            finally:
                db2.close()
        except Exception as e:
            logger.error(f"[HIVE] Error marking task {task_id} in_progress: {e}")

        await self.emit_event("task_started", "hive_poller", agent_name, task_id=task_id)

        logger.info(f"[HIVE] Ejecutando tarea {task_id} para agente sistema: {agent_name}")
        work_dir = executor.get_work_dir(agent_name)
        result = executor.execute(
            agent_name=agent_name,
            task_description=task_desc,
            task_id=task_id,
            work_dir=work_dir,
            log_prefix="hive_sistema",
        )

        outcome = "completed" if result["status"] == "completed" else "failed"
        result_text = f"stdout: {result.get('stdout', '')[:3000]}\nstderr: {result.get('stderr', '')[:1000]}"

        await self.mark_task_outcome(task_id, outcome, result_text)
        await self.emit_event(
            f"task_{outcome}",
            agent_name,
            payload=result_text[:500],
            task_id=task_id,
            outcome=outcome,
        )

        if outcome == "completed":
            logger.info(f"[HIVE] Tarea sistema {task_id} completada por {agent_name}")
        else:
            logger.warning(f"[HIVE] Tarea sistema {task_id} fallida por {agent_name}")

    def stop(self):
        self._running = False
        logger.info("[HIVE] Polling loop stopped")


hive = HiveOrchestrator()
