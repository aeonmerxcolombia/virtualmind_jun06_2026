import asyncio
import psutil
import json
import sqlite3
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.colmena.config import settings
from app.colmena.tools import create_colmena_tools, ToolRegistry

logger = logging.getLogger("colmena.orchestrator")


def _init_eventbus_db():
    db_path = settings.SQLITE_DB_PATH.replace(".db", "_events.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS eventbus_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                source TEXT,
                target TEXT,
                payload TEXT,
                task_id INTEGER,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    return db_path


class EventBusColmena:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self._consumers = []
        self._running = False
        self._db_path = _init_eventbus_db()

    async def emit_event(self, event: Dict[str, Any]):
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO eventbus_log (event_type, source, target, payload, task_id, outcome) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        event.get("type", "unknown"),
                        event.get("source"),
                        event.get("target"),
                        json.dumps(event.get("payload", {})),
                        event.get("task_id"),
                        event.get("outcome"),
                    )
                )
                conn.commit()
        except Exception as e:
            logger.error(f"EventBus persist error: {e}")
        await self.queue.put(event)

    def register_consumer(self, callback):
        self._consumers.append(callback)

    async def start_consumer_loop(self):
        self._running = True
        while self._running:
            try:
                event = await self.queue.get()
                for cb in self._consumers:
                    try:
                        if asyncio.iscoroutinefunction(cb):
                            await cb(event)
                        else:
                            cb(event)
                    except Exception as e:
                        logger.error(f"EventBus consumer error: {e}")
            except Exception as e:
                logger.error(f"EventBus loop error: {e}")

    def stop(self):
        self._running = False


class ExperienceGraph:
    def __init__(self):
        self.db_path = settings.SQLITE_DB_PATH + ".experience"
        self._init_sqlite()

    def _init_sqlite(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experience_graph (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intent_pattern TEXT,
                    strategy TEXT,
                    outcome TEXT,
                    role TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def store_experience(self, intent: str, strategy: str, outcome: str, role: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO experience_graph (intent_pattern, strategy, outcome, role) VALUES (?, ?, ?, ?);",
                (intent, strategy, outcome, role)
            )
            conn.commit()

    def retrieve_experiences(self, intent: str, role: str, limit: int = 3) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT strategy FROM experience_graph WHERE role = ? AND intent_pattern LIKE ? AND outcome = 'success' ORDER BY timestamp DESC LIMIT ?",
                (role, f"%{intent}%", limit)
            )
            return [row[0] for row in cursor.fetchall()]


class InsectoPlanificador:
    def __init__(self):
        self.throttling_delay = 0.001

    async def get_hardware_telemetry(self) -> Dict[str, Any]:
        return {
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent,
            "system_stress_critical": psutil.cpu_percent() > 90 or psutil.virtual_memory().percent > 90
        }


class HibernadorSinaptico:
    def __init__(self):
        self.db_path = settings.SQLITE_DB_PATH
        self._init_sqlite()

    def _init_sqlite(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hibernation_cache (
                    role VARCHAR(50) PRIMARY KEY,
                    serialized_context TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def hibernate_agent(self, role: str, context_state: Dict[str, Any]):
        serialized = json.dumps(context_state)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO hibernation_cache (role, serialized_context)
                VALUES (?, ?);
            """, (role, serialized))
            conn.commit()
        print(f"[HIBERNACION] Canal del rol '{role}' congelado y persistido en SQLite. RAM Liberada.")

    def restore_agent(self, role: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT serialized_context FROM hibernation_cache WHERE role = ?;", (role,))
            row = cursor.fetchone()
            if row:
                state = json.loads(row[0])
                cursor.execute("DELETE FROM hibernation_cache WHERE role = ?;", (role,))
                conn.commit()
                print(f"[DESPERTAR] Contexto del rol '{role}' restaurado con exito en RAM.")
                return state
        return {}


# Singletons
event_bus = EventBusColmena()
experience_graph = ExperienceGraph()


class AgentBrain:
    def __init__(self, token: str = None):
        self.tools: ToolRegistry = create_colmena_tools(token=token)

    def set_token(self, token: str):
        self.tools.set_token(token)

    def _load_role_skill(self, role: str) -> str:
        try:
            skill_path = f"/home/william/skills/agents/rol_{role}.md"
            if os.path.exists(skill_path):
                with open(skill_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error loading skill for role {role}: {e}")
        return ""

    async def think_and_act(self, prompt: str, role: str, context: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        from app.services.ai.mcp_service import mcp_service

        if token:
            self.set_token(token)

        if not self.tools.bridge:
            return {"type": "error", "message": "No hay token JWT. Inicia sesion primero."}

        history = []
        max_iterations = 8
        current_prompt = prompt

        past_experiences = experience_graph.retrieve_experiences(prompt, role)
        exp_context = "\n".join([f"- {exp}" for exp in past_experiences]) if past_experiences else "No previous experiences found for this intent."

        tools_desc = json.dumps(self.tools.list_tools(role=role), indent=2)
        role_skill = self._load_role_skill(role)
        skill_context = f"\n\nROLE SPECIALIZATION & SKILLS:\n{role_skill}" if role_skill else ""

        system_prompt = (
            f"You are the Colmena Agentic OS Brain v5.0 for role: {role}. "
            f"You are a helpful AI assistant integrated into the VirtualMind LMS platform. "
            f"Your goal is to help the user by executing actions through the available tools."
            f"\n\nAVAILABLE TOOLS:\n{tools_desc}"
            f"{skill_context}"
            f"\n\nPAST EXPERIENCES (Synaptic Memory):\n{exp_context}"
            "\n\nCRITICAL BEHAVIOR RULES:"
            "\n1. STEP BY STEP DATA COLLECTION: When creating entities, you probably don't have all the data. "
            "Call the tool with what you have. If the API returns a validation error about missing required fields, "
            "ask the user for ONE field at a time. Example: 'Ok, el proyecto necesita un nombre. Como deberia llamarse?'"
            "\n2. USE list_available_fields FIRST: Before creating something, show the user what fields are needed."
            "\n3. CONFIRM DESTRUCTIVE ACTIONS: If a tool has requires_confirmation=true, ask the user to confirm before executing."
            "\n4. SEARCH BEFORE CREATE: When a user says 'crea una tarea para Maria', first call search_users to find Maria's user ID."
            "\n5. BE CONVERSATIONAL: Respond in Spanish naturally. Explain what you're doing."
            "\n6. HANDLE ERRORS: If a tool returns an error, explain it to the user and suggest how to fix it."
            "\n7. RESPECT PERMISSIONS: If the API returns 403, tell the user they don't have permission."
            "\n\nRESPONSE FORMAT:"
            "\nRespond EXACTLY in one of these JSON formats (no markdown fences):"
            '\n{"thought": "...", "action": "tool_name", "parameters": {"param1": "value1"}}'
            '\n{"thought": "...", "final_answer": "Your response to the user in Spanish."}'
            "\n\nIf you need to ask the user a question, use final_answer with your question."
        )

        for i in range(max_iterations):
            full_prompt = f"Context: {json.dumps(context)}\n\nHistory:\n" + "\n".join(history) + f"\n\nUser: {current_prompt}"
            model_to_use = settings.MODEL_COMPLEX if i == 0 else settings.MODEL_FAST

            await event_bus.emit_event({"type": "brain_cogitation", "role": role, "iteration": i, "prompt": current_prompt})

            try:
                result = mcp_service.generate_json(
                    prompt=full_prompt,
                    system_instruction=system_prompt,
                    temperature=0.2,
                    model=model_to_use
                )
            except Exception as e:
                logger.error(f"LLM generation error: {e}")
                return {"type": "error", "message": f"Error generando respuesta: {e}"}

            try:
                res_json = json.loads(result) if isinstance(result, str) else result
                thought = res_json.get("thought", "")

                if "final_answer" in res_json:
                    experience_graph.store_experience(
                        prompt,
                        " -> ".join([h.split("Action:")[0] for h in history]) if history else "direct_answer",
                        "success", role
                    )
                    await event_bus.emit_event({"type": "brain_conclusion", "role": role, "answer": res_json["final_answer"]})
                    return {"type": "agent_response", "message": res_json["final_answer"], "thought": thought, "iterations": i + 1}

                action = res_json.get("action")
                params = res_json.get("parameters", {})

                if not action:
                    if thought:
                        return {"type": "agent_response", "message": thought, "thought": "Implicit answer", "iterations": i + 1}
                    return {"type": "error", "message": "No se pudo determinar la accion a tomar."}

                await event_bus.emit_event({"type": "brain_action", "role": role, "action": action, "parameters": params})

                tool = self.tools.get_tool(action)
                if not tool:
                    observation = f"Error: La herramienta '{action}' no existe. Las herramientas disponibles son: {list(self.tools.tools.keys())}"
                else:
                    observation = await tool.execute(self.tools.bridge, **params)

                history.append(f"Thought: {thought}\nAction: {action}({params})\nObservation: {json.dumps(observation, ensure_ascii=False)}")
                current_prompt = "Based on the observation, decide: if the result has data, present it to the user. If there's a validation error, ask the user for the missing field. If the action succeeded, tell the user what happened."

            except Exception as e:
                logger.error(f"AgentBrain loop error: {e}")
                return {"type": "error", "message": f"Error interno del agente: {e}"}

        return {"type": "error", "message": "Maximo de iteraciones alcanzado. Se necesitan mas datos."}
