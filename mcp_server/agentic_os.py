"""
Agentic OS Core — Multi-step planning, parallel execution, contextual memory, rollback.

Arquitectura:
- AgentOrchestrator: planifica y ejecuta workflows multi-paso
- MemoryContext: memoria contextual de sesión (entidades, errores, preferencias)
- AgentPlan: plan con grafo de dependencias entre pasos
- RollbackManager: deshace pasos completados ante fallos críticos
"""

import json
import re
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AgentStep:
    id: int
    tool_name: str
    params: dict
    description: str = ""
    depends_on: list[int] = field(default_factory=list)
    status: str = "pending"  # pending | running | success | failed | skipped | rolled_back
    result: Any = None
    error: str = ""
    critical: bool = True  # if True, failure triggers rollback of prior steps


@dataclass
class AgentPlan:
    steps: list[AgentStep] = field(default_factory=list)
    context: dict = field(default_factory=dict)  # shared context across steps
    parallel_groups: list[list[int]] = field(default_factory=list)


@dataclass
class MemoryContext:
    session_id: str = ""
    user_id: str = ""
    user_name: str = ""
    recent_clients: list[dict] = field(default_factory=list)
    recent_projects: list[dict] = field(default_factory=list)
    recent_users: list[dict] = field(default_factory=list)
    error_history: list[dict] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    entity_cache: dict = field(default_factory=dict)

    def track_entity(self, type_: str, data: dict):
        lst = getattr(self, f"recent_{type_}", None)
        if lst is not None:
            name = data.get("name") or data.get("razon_social") or data.get("nombre") or str(data.get("id", ""))
            exists = any(e.get("id") == data.get("id") for e in lst)
            if not exists:
                lst.insert(0, data)
                if len(lst) > 10:
                    lst.pop()

    def track_error(self, tool: str, error: str, params: dict = None):
        self.error_history.append({
            "tool": tool,
            "error": error,
            "params": params,
            "time": datetime.now().isoformat()
        })
        if len(self.error_history) > 20:
            self.error_history.pop(0)

    def get_context_prompt(self) -> str:
        lines = []
        if self.recent_clients:
            names = [c.get("razon_social", "?") for c in self.recent_clients[:3]]
            lines.append(f"  - Clientes recientes: {', '.join(names)}")
        if self.recent_projects:
            names = [p.get("name", "?") for p in self.recent_projects[:3]]
            lines.append(f"  - Proyectos recientes: {', '.join(names)}")
        if self.user_name:
            lines.append(f"  - Usuario actual: {self.user_name}")
        if self.error_history:
            last = self.error_history[-1]
            lines.append(f"  - Último error: {last['tool']}: {last['error'][:100]}")
        return "\n".join(lines)


class RollbackManager:
    """Manages rollback of completed steps."""

    ROLLBACK_MAP = {
        "create_project": ("delete_project", ("project_id", "project_id")),
        "create_user": ("delete_user", ("user_id", "user_id")),
        "create_client": ("delete_client", ("client_id", "client_id")),
        "create_task": ("delete_task", ("task_id", "task_id")),
        "assign_role": None,
    }

    def __init__(self, call_tool_fn):
        self._call_tool = call_tool_fn

    async def rollback(self, plan: AgentPlan, up_to_step: int):
        """Roll back completed steps before up_to_step, in reverse order."""
        for step in reversed(plan.steps[:up_to_step]):
            if step.status != "success":
                continue
            rollback_info = self.ROLLBACK_MAP.get(step.tool_name)
            if rollback_info is None:
                continue
            rb_tool, (result_field, param_field) = rollback_info
            result = step.result or {}
            if isinstance(result, dict):
                rb_id = result.get(result_field)
                if rb_id:
                    try:
                        await self._call_tool(rb_tool, {param_field: rb_id})
                        step.status = "rolled_back"
                    except Exception as e:
                        pass

    def can_rollback(self, step: AgentStep) -> bool:
        return step.tool_name in self.ROLLBACK_MAP


class AgentOrchestrator:
    """Central agent that plans and executes multi-step workflows."""

    def __init__(self, session, memory: MemoryContext, call_tool_fn, resolve_names_fn):
        self.session = session
        self.memory = memory
        self._call_tool = call_tool_fn
        self._resolve_names = resolve_names_fn
        self.rollback_mgr = RollbackManager(call_tool_fn)

    async def create_plan(self, gemini_response: str) -> Optional[AgentPlan]:
        """Parse ##PLAN## from Gemini response into an AgentPlan."""
        plan_match = re.search(r"##PLAN##\s*(\[.*?\])\s*##END##", gemini_response, re.DOTALL)
        if not plan_match:
            return None

        try:
            steps_data = json.loads(plan_match.group(1))
        except json.JSONDecodeError:
            return None

        plan = AgentPlan()
        for i, sd in enumerate(steps_data):
            step = AgentStep(
                id=i,
                tool_name=sd.get("tool", ""),
                params=sd.get("params", {}),
                description=sd.get("description", ""),
                depends_on=sd.get("depends_on", []),
                critical=sd.get("critical", True),
            )
            plan.steps.append(step)

        plan.parallel_groups = self._build_parallel_groups(plan)
        return plan

    def _build_parallel_groups(self, plan: AgentPlan) -> list[list[int]]:
        """Group steps by dependency level for parallel execution."""
        levels = {}
        for step in plan.steps:
            if not step.depends_on:
                levels[step.id] = 0
            else:
                levels[step.id] = max(levels.get(d, 0) for d in step.depends_on) + 1

        groups = {}
        for sid, lvl in levels.items():
            groups.setdefault(lvl, []).append(sid)
        return [groups[k] for k in sorted(groups.keys())]

    def _resolve_refs(self, params: dict, plan: AgentPlan) -> dict:
        """Resolve ${step_index.field} references in params."""
        resolved = {}
        for k, v in params.items():
            if isinstance(v, str):
                refs = re.findall(r"\{(\d+)\.([^}]+)\}", v)
                if refs:
                    for ref_step, ref_field in refs:
                        ref_step = int(ref_step)
                        if ref_step < len(plan.steps):
                            step_result = plan.steps[ref_step].result or {}
                            if isinstance(step_result, dict):
                                val = str(step_result.get(ref_field, ""))
                                v = v.replace(f"{{{ref_step}.{ref_field}}}", val)
                resolved[k] = v
            else:
                resolved[k] = v
        return resolved

    async def execute_plan(self, plan: AgentPlan) -> AgentPlan:
        for group_idx, group in enumerate(plan.parallel_groups):
            tasks = {}
            for step_id in group:
                step = plan.steps[step_id]
                step.status = "running"

                resolved_params = self._resolve_refs(step.params, plan)
                resolved_params = await self._resolve_names(resolved_params)

                tasks[step_id] = self._execute_single(step, resolved_params)

            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            for step_id, result in zip(tasks.keys(), results):
                step = plan.steps[step_id]
                if isinstance(result, Exception):
                    step.status = "failed"
                    step.error = str(result)
                    self.memory.track_error(step.tool_name, str(result), step.params)
                    if step.critical:
                        await self.rollback_mgr.rollback(plan, step_id)
                        for s in plan.steps:
                            if s.status == "pending":
                                s.status = "skipped"
                        return plan
                elif isinstance(result, dict) and "error" in result:
                    step.status = "failed"
                    step.error = result["error"]
                    self.memory.track_error(step.tool_name, result["error"], step.params)
                    if step.critical:
                        await self.rollback_mgr.rollback(plan, step_id)
                        for s in plan.steps:
                            if s.status == "pending":
                                s.status = "skipped"
                        return plan
                else:
                    step.status = "success"
                    step.result = result
                    self._update_memory(step)

        return plan

    async def _execute_single(self, step: AgentStep, params: dict) -> Any:
        return await self._call_tool(step.tool_name, params)

    def _update_memory(self, step: AgentStep):
        result = step.result or {}
        if isinstance(result, dict):
            if "razon_social" in result:
                self.memory.track_entity("clients", result)
            if result.get("project_id") or result.get("id"):
                name = result.get("name") or result.get("razon_social") or ""
                if name:
                    self.memory.track_entity("projects", {"id": result.get("id") or result.get("project_id"), "name": name})
            if "email" in result:
                self.memory.track_entity("users", result)


PLANNING_SYSTEM_PROMPT = """Eres un agente de planificación del sistema VirtualMind. Tu trabajo es ayudar al usuario a realizar tareas complejas usando las herramientas disponibles.

CAPACIDADES:
- Puedes ejecutar UNA herramienta por paso
- Puedes crear planes de MÚLTIPLES pasos con dependencias
- Los pasos independientes se ejecutan en PARALELO
- Cuando el usuario pide múltiples acciones (ej: "crea proyecto Y asigna coordinador"), DEBES crear un plan con TODOS los pasos
- Puedes preguntar información faltante antes de crear el plan

REGLAS PARA ID vs NOMBRE:
- Para parámetros que terminan en '_id' o son 'user_uid':
  NUNCA preguntes por IDs. Usa el NOMBRE en su lugar.
  El servidor resolverá automáticamente: nombre -> ID.
  - client_id → usa client_name (ej: "Banco Agrario")
  - user_id, user_uid → usa user_name (ej: "María García")
  - project_id → usa project_name (ej: "Curso Python")

REGLAS DE CONVERSACIÓN:
1. Recibe la solicitud del usuario. Si ya tiene TODOS los datos, pasa directo al plan.
2. Si faltan datos, pregunta de forma natural (UN dato a la vez)
3. Cuando tengas toda la información, presenta el plan completo al usuario
4. Pide confirmación antes de ejecutar
5. Si el usuario confirma, emite ##PLAN## con el JSON del plan

REGLAS DEL PLAN:
1. INCLUYE TODAS las acciones en el plan. Si el usuario pide "crear proyecto y asignar coordinador", el plan debe tener 4 pasos (buscar cliente, buscar usuario, crear proyecto, asignar participante)
2. Cada paso ejecuta UNA herramienta
3. Identifica dependencias: paso B necesita datos del paso A → depends_on: [A]
4. Pasos sin depends_on entre sí se ejecutan en paralelo
5. Los pasos de búsqueda no son críticos (critical: false). Los pasos de creación/asignación son críticos (critical: true)

FORMATO DE RESPUESTA ##PLAN##:
##PLAN##
[
  {{
    "tool": "search_clients",
    "params": {{"query": "nombre_del_cliente"}},
    "description": "Buscar el cliente en el sistema",
    "depends_on": [],
    "critical": false
  }},
  {{
    "tool": "create_project",
    "params": {{
      "name": "nombre_proyecto",
      "client_name": "nombre_del_cliente",
      "tipo_proyecto": "e-learning",
      "start_date": "2026-07-01"
    }},
    "description": "Crear el proyecto",
    "depends_on": [0],
    "critical": true
  }}
]
##END##

EJEMPLO COMPLETO (4 pasos):

User: crea un proyecto e-learning para el Banco Agrario, llamalo Curso Compliance, que empiece el 1 de julio y asigna a María García como coordinadora
Tú: Perfecto, creé este plan:
1. Buscar al cliente "Banco Agrario"
2. Buscar a la usuaria "María García"
3. Crear el proyecto "Curso Compliance" para el Banco Agrario
4. Asignar a María García como coordinadora del proyecto

¿Confirmo la ejecución?
User: sí
Tú: ##PLAN##
[
  {{"tool": "search_clients", "params": {{"query": "Banco Agrario"}}, "description": "Buscar el cliente", "depends_on": [], "critical": false}},
  {{"tool": "search_users", "params": {{"query": "María García"}}, "description": "Buscar a la coordinadora", "depends_on": [], "critical": false}},
  {{"tool": "create_project", "params": {{"name": "Curso Compliance", "client_name": "Banco Agrario", "tipo_proyecto": "e-learning", "start_date": "2026-07-01"}}, "description": "Crear el proyecto", "depends_on": [0], "critical": true}},
  {{"tool": "add_participant", "params": {{"project_id": "{2.project_id}", "user_name": "María García", "role_id": 1}}, "description": "Asignar coordinadora al proyecto", "depends_on": [1, 2], "critical": true}}
]
##END##

IMPORTANTE: usa referencias {indice.campo} cuando necesites pasar IDs entre pasos. 
Ej: {2.project_id} toma el project_id del paso 2 (create_project).
Ej: {1.uid} toma el uid del paso 1 (search_users).
Ej: en JSON: "project_id": "{2.project_id}"
"""
