import json
import logging
import asyncio
import importlib
import re
from decimal import Decimal
from datetime import date, datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from fastapi import WebSocket

from app.colmena.config import settings
from app.colmena.security import AgentContext


def serialize_value(v: Any) -> Any:
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, set):
        return list(v)
    return v


logger = logging.getLogger("colmena.dispatcher")


@dataclass
class CommandIntent:
    action_type: str = "unknown"
    entity_type: str = ""
    parameters: dict = field(default_factory=dict)
    confidence: float = 0.0
    reason: str = ""


class DispatcherError(Exception):
    pass


ENTITY_HIERARCHY = {
    "project": {"parent": None, "label": "proyecto", "next": "study_plan"},
    "study_plan": {"parent": "project", "label": "plan de estudio", "next": "module"},
    "module": {"parent": "study_plan", "label": "módulo", "next": "unit"},
    "unit": {"parent": "module", "label": "unidad", "next": "learning_activity"},
    "learning_activity": {"parent": "unit", "label": "actividad de aprendizaje", "next": None},
    "task": {"parent": "project", "label": "tarea", "next": None},
    "evaluation": {"parent": "module", "label": "evaluación", "next": None},
}

ACTION_PATTERNS = {
    "query": [r"\b(muestra|lista|ver|consulta|busca|encuentra|dame|obtén|obten|trae|cuales|que\s+hay)\b"],
    "mutate": [r"\b(crea|nuev[oa]|añade|agrega|inserta|actualiza|edita|modifica|elimina|borra|cambia)\b"],
    "background": [r"\b(genera|produce|haz|renderiza|sintetiza|crea\s+(un\s+)?(video|imagen|audio|podcast))\b"],
}

ENTITY_PATTERNS = {
    "project": [r"\bproyectos?\b", r"\bcursos?\b"],
    "unit": [r"\bunidades?\b", r"\bunidad\b"],
    "module": [r"\bmódulos?\b", r"\bmodulos?\b"],
    "learning_activity": [r"\bactividades?\s+de\s+aprendizaje\b", r"\blearning\s+activities?\b"],
    "study_plan": [r"\bplan(es)?\s+de\s+(formación|estudio|formacion)\b"],
    "task": [r"\btareas?\b"],
    "evaluation": [r"\bevaluaciones?\b", r"\bevaluacion(es)?\b"],
    "video": [r"\bvideos?\b"],
}


class IntentClassifier:
    @staticmethod
    def classify_keyword(command: str) -> Optional[CommandIntent]:
        cmd_lower = command.lower()
        action_type = "unknown"
        entity_type = ""
        confidence = 0.0

        for atype, patterns in ACTION_PATTERNS.items():
            for p in patterns:
                if re.search(p, cmd_lower):
                    action_type = atype
                    confidence = 0.7
                    break
            if confidence > 0:
                break

        for etype, patterns in ENTITY_PATTERNS.items():
            for p in patterns:
                if re.search(p, cmd_lower):
                    entity_type = etype
                    confidence = min(confidence + 0.15, 0.95)
                    break
            if entity_type:
                break

        if confidence > 0:
            if action_type in ("mutate", "query") and not entity_type:
                logger.info(f"Keyword matched action={action_type} but no entity, falling back to Gemini")
                return None
            params = IntentClassifier.parse_entity_fields(command)
            return CommandIntent(
                action_type=action_type,
                entity_type=entity_type,
                parameters=params,
                confidence=confidence,
                reason="keyword_match",
            )
        return None

    @staticmethod
    def parse_entity_fields(command: str) -> dict:
        params = {}
        m = re.search(r'llamad[ao]\s+"([^"]+)"', command)
        if m: params["nombre"] = m.group(1)
        m = re.search(r'llamad[ao]\s+([\w\s]+?)(?:\s+para|\s+del\s+|\s+en\s+|\s*$)', command)
        if not m: m = re.search(r'(?:nuev[oa]\s+(?:proyecto|plan|módulo|unidad|curso)\s+llamad[ao]\s+|crea\s+(?:un\s+)?(?:proyecto|plan|módulo|unidad|curso)\s+llamad[ao]\s+)"?([^"]+)"?', command)
        if not m: m = re.search(r'(?:con\s+)?(?:nombre|título|titulo|title)\s*[=:]\s*"?([^",]+)"?', command)
        if m and "nombre" not in params:
            maybe = m.group(1).strip()
            if maybe and len(maybe) < 100:
                params["nombre"] = maybe
        m = re.search(r'(?:para\s+(?:el\s+)?(?:cliente|client)\s+|cliente\s*[=:]\s*)"?([^"]+)"?', command)
        if m: params["cliente"] = m.group(1).strip()
        parent_patterns = [
            (r'(?:para\s+)?(?:el\s+)?proyecto\s+(\d+)', 'project_id'),
            (r'(?:para\s+)?(?:el\s+)?plan\s+de\s+(?:estudio|formaci[óo]n)\s+(\d+)', 'study_plan_id'),
            (r'(?:para\s+)?(?:el\s+)?plan\s+(\d+)', 'study_plan_id'),
            (r'(?:para\s+)?(?:el\s+)?m[óo]dulo\s+(\d+)', 'module_id'),
            (r'(?:para\s+)?(?:el\s+)?unidad\s+(\d+)', 'unit_id'),
        ]
        for pattern, field in parent_patterns:
            if field not in params:
                m = re.search(pattern, command, re.IGNORECASE)
                if m:
                    params[field] = int(m.group(1))
        return params

    @staticmethod
    async def classify_gemini(command: str, role: str) -> Optional[CommandIntent]:
        try:
            from app.services.ai.mcp_service import mcp_service
            fallback_params = IntentClassifier.parse_entity_fields(command)
            result = mcp_service.generate_json(
                prompt=f"Classify this command from a {role} user in an LMS. "
                       f"Command: '{command}'. "
                       f"Return JSON with fields: "
                       f"action_type (\"query\"|\"mutate\"|\"background\"|\"unknown\"), "
                       f"entity_type (\"project\"|\"unit\"|\"module\"|\"learning_activity\"|\"study_plan\"|\"task\"|\"evaluation\"|\"video\"|\"\"), "
                       f"parameters (object with entity fields extracted from the command, e.g. {{\"nombre\":\"...\", \"cliente\":\"...\"}}), "
                       f"confidence (0.0-1.0), reason (\"...\")",
                system_instruction="You are an intent classifier. Extract entity fields from the command. Respond only with valid JSON.",
                temperature=0.1,
                max_tokens=512,
            )
            if result and result.get("action_type") in ("query", "mutate", "background"):
                params = result.get("parameters", {}) or {}
                if not params:
                    params = fallback_params
                return CommandIntent(
                    action_type=result["action_type"],
                    entity_type=result.get("entity_type", ""),
                    parameters=params,
                    confidence=result.get("confidence", 0.5),
                    reason=result.get("reason", "gemini_classified"),
                )
        except Exception as e:
            logger.warning(f"Gemini classification failed: {e}")
        return None

    @staticmethod
    async def classify(command: str, role: str) -> CommandIntent:
        kw = IntentClassifier.classify_keyword(command)
        if kw:
            logger.info(f"Keyword match: {kw}")
            return kw
        gemini = await IntentClassifier.classify_gemini(command, role)
        if gemini:
            logger.info(f"Gemini match: {gemini}")
            return gemini
        return CommandIntent(action_type="unknown", reason="no_match")


class MCPHandler:
    ENTITY_MODEL_MAP: Dict[str, str] = {
        "unit": "app.models.unit.Unit",
        "module": "app.models.module.Module",
        "project": "app.models.project.Project",
        "study_plan": "app.models.study_plan.StudyPlan",
        "learning_activity": "app.models.learning_activity.LearningActivity",
        "task": "app.models.tarea.Tarea",
        "evaluation": "app.models.evaluacion.Evaluacion",
        "course": "app.models.module.Module",
    }

    FIELD_MAP: Dict[str, Dict[str, str]] = {
        "project": {"nombre": "name", "name": "name", "cliente": "client_id"},
        "study_plan": {"nombre": "name", "name": "name"},
        "module": {"nombre": "nombre_del_modulo", "name": "nombre_del_modulo"},
        "unit": {"nombre": "name", "name": "name"},
        "learning_activity": {"nombre": "nombre", "name": "nombre"},
        "task": {"nombre": "titulo", "name": "titulo"},
        "evaluation": {"nombre": "titulo", "name": "titulo"},
    }

    @classmethod
    def _get_model(cls, entity_type: str):
        path = cls.ENTITY_MODEL_MAP.get(entity_type)
        if not path:
            raise DispatcherError(f"Entity type '{entity_type}' not supported")
        mod_path, cls_name = path.rsplit(".", 1)
        mod = importlib.import_module(mod_path)
        return getattr(mod, cls_name)

    @staticmethod
    def query(entity_type: str, filters: dict, limit: int = 20) -> list:
        from app.database.db import SessionLocal
        model = MCPHandler._get_model(entity_type)
        db: Session = SessionLocal()
        try:
            q = db.query(model)
            for k, v in filters.items():
                if hasattr(model, k):
                    q = q.filter(getattr(model, k) == v)
            results = q.limit(limit).all()
            cleaned = []
            for r in results:
                row = {c.name: serialize_value(getattr(r, c.name)) for c in r.__table__.columns}
                cleaned.append(row)
            return cleaned
        finally:
            db.close()

    @staticmethod
    def _resolve_client_id(name_or_id: str) -> Optional[str]:
        from app.database.db import SessionLocal
        import uuid
        try:
            uuid.UUID(str(name_or_id))
            return name_or_id
        except (ValueError, AttributeError):
            pass
        from app.models.user import User
        db = SessionLocal()
        try:
            user = db.query(User).filter(
                (User.nombre == name_or_id) | (User.email == name_or_id)
            ).first()
            if user:
                return str(user.uid)
            user = db.query(User).filter(User.nombre.like(f"%{name_or_id}%")).first()
            if user:
                return str(user.uid)
        finally:
            db.close()
        return None

    @staticmethod
    def create(entity_type: str, data: dict) -> dict:
        from app.database.db import SessionLocal
        from datetime import date
        import uuid
        model = MCPHandler._get_model(entity_type)
        column_names = {c.name for c in model.__table__.columns}
        defaults = {
            "project": {"estado": "Planificado", "start_date": date.today().isoformat()},
            "study_plan": {},
            "module": {},
            "unit": {},
            "learning_activity": {},
            "task": {},
            "evaluation": {},
        }
        merged = dict(defaults.get(entity_type, {}))
        for k, v in data.items():
            if k not in column_names:
                continue
            if k == "client_id":
                resolved = MCPHandler._resolve_client_id(v)
                if not resolved:
                    raise DispatcherError(
                        f"No encontré ningún usuario llamado \"{v}\". Usa el email o nombre exacto del cliente."
                    )
                merged[k] = resolved
                continue
            merged[k] = v
        if entity_type == "unit":
            if "short_name" not in merged and "name" in merged:
                merged["short_name"] = merged["name"][:100]
            if "general_objective" not in merged:
                merged["general_objective"] = f"Objetivo general de {merged.get('name', 'la unidad')}"
        db: Session = SessionLocal()
        try:
            instance = model(**merged)
            db.add(instance)
            db.commit()
            db.refresh(instance)
            return {k: serialize_value(v) for k, v in instance.__dict__.items() if not k.startswith("_")}
        except Exception as e:
            db.rollback()
            raise DispatcherError(f"Error creating {entity_type}: {e}")
        finally:
            db.close()

    @staticmethod
    def update(entity_type: str, entity_id: int, data: dict) -> dict:
        from app.database.db import SessionLocal
        model = MCPHandler._get_model(entity_type)
        db: Session = SessionLocal()
        try:
            instance = db.query(model).filter(model.id == entity_id).first()
            if not instance:
                raise DispatcherError(f"{entity_type} with id {entity_id} not found")
            for k, v in data.items():
                if hasattr(instance, k):
                    setattr(instance, k, v)
            db.commit()
            db.refresh(instance)
            return {k: v for k, v in instance.__dict__.items() if not k.startswith("_")}
        except DispatcherError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise DispatcherError(f"Error updating {entity_type}: {e}")
        finally:
            db.close()

    @staticmethod
    def delete(entity_type: str, entity_id: int) -> bool:
        from app.database.db import SessionLocal
        model = MCPHandler._get_model(entity_type)
        db: Session = SessionLocal()
        try:
            instance = db.query(model).filter(model.id == entity_id).first()
            if not instance:
                raise DispatcherError(f"{entity_type} with id {entity_id} not found")
            db.delete(instance)
            db.commit()
            return True
        except DispatcherError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise DispatcherError(f"Error deleting {entity_type}: {e}")
        finally:
            db.close()

    @staticmethod
    def execute_raw_sql(sql: str, params: dict = None) -> List[Any]:
        """Executes a raw SQL query on the database. ONLY for SuperAdmin roles."""
        from app.database.db import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            result = db.execute(text(sql), params or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            db.commit()
            return [{"status": "success", "rows_affected": result.rowcount}]
        except Exception as e:
            db.rollback()
            raise DispatcherError(f"SQL Execution Error: {e}")
        finally:
            db.close()


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, List[WebSocket]] = {}

    def add(self, role: str, ws: WebSocket):
        if role not in self._connections:
            self._connections[role] = []
        self._connections[role].append(ws)

    def remove(self, role: str, ws: WebSocket):
        if role in self._connections:
            self._connections[role] = [w for w in self._connections[role] if w != ws]
            if not self._connections[role]:
                del self._connections[role]

    async def notify_role(self, role: str, message: dict):
        if role not in self._connections:
            return
        dead = []
        for ws in self._connections[role]:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.remove(role, ws)

    async def broadcast(self, message: dict):
        for role in list(self._connections.keys()):
            await self.notify_role(role, message)


connection_manager = ConnectionManager()


class Dispatcher:
    def __init__(self):
        self.mcp = MCPHandler()

    async def dispatch(
        self,
        command: str,
        role: str,
        context: AgentContext,
        websocket: WebSocket,
    ) -> dict:
        logger.info(f"Dispatching command: {command} for role: {role}")
        
        from app.colmena.orchestrator import AgentBrain
        brain = AgentBrain(token=context.token)
        result = await brain.think_and_act(
            prompt=command,
            role=role,
            context={"user_id": context.user_id, "roles": context.roles, "email": context.email},
            token=context.token,
        )
        
        return result

    @staticmethod
    def _format_project_row(r: dict) -> str:
        nombre = r.get("nombre_proyecto", r.get("nombre", r.get("name", "?")))
        estado = r.get("estado", r.get("status", "?"))
        cliente = r.get("cliente", "")
        fecha = r.get("fecha_inicio", r.get("created_at", ""))
        if isinstance(fecha, str) and len(fecha) > 10: fecha = fecha[:10]
        presupuesto = r.get("presupuesto", "")
        pct = r.get("porcentaje", "")
        progre = f" [{pct}%]" if pct else ""
        c = f" · {cliente}" if cliente else ""
        p = f" · ${presupuesto}" if presupuesto else ""
        return f"📁 {nombre}{c}{p} — {estado}{progre} ({fecha})"

    @staticmethod
    def _fmt_projects(data: list) -> str:
        if not data: return "   No hay proyectos registrados."
        lines = [f"   {len(data)} proyecto(s):"]
        lines += [Dispatcher._format_project_row(r) for r in data]
        return "\n".join(lines)

    @staticmethod
    def _format_generic(r: dict) -> str:
        name = r.get("nombre", r.get("name", r.get("titulo", r.get("title", "?"))))
        estado = r.get("estado", r.get("status", ""))
        created = r.get("created_at", r.get("fecha_creacion", ""))
        if isinstance(created, str) and len(created) > 10: created = created[:10]
        e = f" — {estado}" if estado else ""
        return f"  • {name}{e} ({created})" if created else f"  • {name}{e}"

    @staticmethod
    def _format_results(entity_type: str, data: list) -> str:
        if entity_type in ("project", "course"):
            return Dispatcher._fmt_projects(data)
        if not data:
            return f"   No hay {entity_type}s registrados."
        lines = [f"   {len(data)} {entity_type}(s):"]
        lines += [Dispatcher._format_generic(r) for r in data]
        return "\n".join(lines)

    async def _handle_query(self, intent: CommandIntent, context: AgentContext) -> dict:
        if not intent.entity_type:
            return {"type": "error", "message": "Especifica qué quieres consultar (unidades, módulos, proyectos, etc.)"}
        try:
            filters = intent.parameters.get("filters", {})
            results = self.mcp.query(intent.entity_type, filters)
            return {
                "type": "query_result",
                "entity_type": intent.entity_type,
                "count": len(results),
                "data": results,
                "formatted": self._format_results(intent.entity_type, results),
            }
        except DispatcherError as e:
            return {"type": "error", "message": str(e)}

    async def _handle_mutate(self, intent: CommandIntent, context: AgentContext) -> dict:
        if not intent.entity_type:
            return {"type": "error", "message": "Especifica qué entidad quieres modificar"}
        try:
            data = intent.parameters.get("data", intent.parameters)
            field_map = self.mcp.FIELD_MAP.get(intent.entity_type, {})
            mapped = {}
            for k, v in data.items():
                mapped_key = field_map.get(k, k)
                mapped[mapped_key] = v
            data = mapped
            entity_id = intent.parameters.get("id")
            if entity_id:
                result = self.mcp.update(intent.entity_type, entity_id, data)
                name = result.get("nombre", result.get("name", result.get("titulo", str(entity_id))))
                return {
                    "type": "mutate_result", "action": "update",
                    "entity_type": intent.entity_type, "data": result,
                    "formatted": f"✅ {intent.entity_type} \"{name}\" actualizado",
                }
            else:
                result = self.mcp.create(intent.entity_type, data)
                name = result.get("nombre", result.get("name", result.get("titulo", str(result.get("id", "?")))))
                return {
                    "type": "mutate_result", "action": "create",
                    "entity_type": intent.entity_type, "data": result,
                    "formatted": f"✅ {intent.entity_type} \"{name}\" creado (ID: {result.get('id', '?')})",
                }
        except DispatcherError as e:
            return {"type": "error", "message": str(e)}

    async def _handle_background(self, intent: CommandIntent, context: AgentContext, websocket: WebSocket) -> dict:
        task_type = _map_entity_to_task_type(intent.entity_type)
        from app.colmena.tasks import run_multimedia_task_and_notify
        asyncio.ensure_future(
            run_multimedia_task_and_notify(
                task_type=task_type,
                prompt=intent.parameters.get("prompt", intent.reason or "genera contenido educativo"),
                user_id=context.user_id,
                role=context.roles[0] if context.roles else "unknown",
            )
        )
        return {
            "type": "background_started",
            "message": f"Tarea {task_type} iniciada",
            "entity_type": intent.entity_type,
        }


def _map_entity_to_task_type(entity_type: str) -> str:
    video_types = {"video"}
    audio_types = {"audio", "podcast"}
    image_types = {"image", "imagen"}
    if entity_type in video_types:
        return "video"
    if entity_type in audio_types:
        return "audio"
    if entity_type in image_types:
        return "image"
    return "text"


dispatcher = Dispatcher()
