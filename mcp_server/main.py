"""
MCP Server para VirtualMind
Expone herramientas de IA conectadas a la base de datos
"""

import sys

sys.path.insert(0, "/home/ubuntu/backend")

import json
import os
import re
import asyncio
import httpx
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from sse_starlette.sse import EventSourceResponse

from mcp_server.tools import (
    projects,
    users,
    courses,
    tasks,
    clients,
    content,
    analytics,
)
from mcp_server.tools.ai import generate_with_ai
from mcp_server.agentic_os import (
    AgentOrchestrator,
    MemoryContext,
    PLANNING_SYSTEM_PROMPT,
)

app = FastAPI(
    title="VirtualMind MCP Server",
    description="Servidor MCP con herramientas de IA para VirtualMind",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ToolRequest(BaseModel):
    tool_name: str
    params: Optional[Dict[str, Any]] = None
    token: Optional[str] = None


API_BRIDGE_MAP = {
    "get_all_projects": ("get_projects", True),
    "get_project_by_id": ("get_project", True, "project_id"),
    "search_projects": ("search", True, "query"),
    "create_project": ("create_project", True),
    "update_project": ("update_project", True, "project_id"),
    "delete_project": ("delete_project", True, "project_id"),
    "get_all_users": ("get_users", True),
    "get_user_by_id": ("get_user", True, "user_id"),
    "create_user": ("create_user", True),
    "update_user": ("update_user", True, "user_id"),
    "delete_user": ("delete_user", True, "user_id"),
    "get_all_clients": ("get_clients", True),
    "get_client_by_id": ("get_client", True, "client_id"),
    "create_client": ("create_client", True),
    "update_client": ("update_client", True, "client_id"),
    "delete_client": ("delete_client", True, "client_id"),
    "get_tasks_by_project": ("get_tasks", True),
    "get_task_by_id": ("get_task", True, "task_id"),
    "create_task": ("create_task", True),
    "update_task": ("update_task", True, "task_id"),
    "delete_task": ("delete_task", True, "task_id"),
    "get_fases": ("get_fases", True),
    "get_etapas": ("get_etapas", True),
    "get_cronograma_by_project": ("get_cronogramas", True),
    "add_participant": ("add_participante", True),
    "get_participants": ("get_participantes", True),
}

TOOLS: Dict[str, Any] = {}
TOOL_NAMES: List[str] = []


class NLURequest(BaseModel):
    text: str
    role: str = "superadmin"
    context_id: Optional[str] = None
    token: Optional[str] = None


class NLUResponse(BaseModel):
    corrected_text: str = ""
    intent: str = "unknown"
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = {}
    confidence: float = 0.0
    explanation: str = ""
    response: str = ""
    role: str = ""
    fuzzy_matched: bool = False
    fuzzy_suggestions: List[str] = []


_nlu_contexts: Dict[str, list] = {}


def levenshtein_distance(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[m][n]


def fuzzy_match_tool(query: str, threshold: int = 3) -> List[tuple]:
    query_clean = re.sub(r"[^a-z0-9_]", "", query.lower().replace(" ", "_"))
    scores = []
    for name in TOOL_NAMES:
        dist = levenshtein_distance(query_clean, name)
        if dist <= threshold:
            scores.append((name, dist))
    scores.sort(key=lambda x: x[1])
    return scores[:5]


@app.post("/mcp/nlu", response_model=NLUResponse)
async def mcp_nlu(req: NLURequest):
    text = req.text
    role = req.role
    ctx_id = req.context_id or f"mcp_{role}"
    token = req.token

    if ctx_id not in _nlu_contexts:
        _nlu_contexts[ctx_id] = []

    if token:
        try:
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                nlu_resp = await client.post(
                    "https://localhost:8000/colmena/nlu",
                    json={"text": text, "role": role, "context_id": ctx_id},
                    headers={"Authorization": f"Bearer {token}"},
                )
                if nlu_resp.status_code == 200:
                    data = nlu_resp.json()
                    _nlu_contexts[ctx_id].append(
                        f"User: {text} -> NLU: {data.get('corrected_text', text)}"
                    )
                    tn = data.get("tool_name", "")
                    fuzzy_suggestions = []
                    fuzzy_matched = False
                    if tn and tn not in TOOLS:
                        fuzzy_suggestions = [s[0] for s in fuzzy_match_tool(tn)]
                        if fuzzy_suggestions:
                            fuzzy_matched = True
                            data["tool_name"] = fuzzy_suggestions[0]
                    return NLUResponse(
                        corrected_text=data.get("corrected_text", text),
                        intent=data.get("intent", "unknown"),
                        tool_name=data.get("tool_name", ""),
                        parameters=data.get("parameters", {}),
                        confidence=data.get("confidence", 0.0),
                        explanation=data.get("explanation", ""),
                        response=data.get("response", ""),
                        role=role,
                        fuzzy_matched=fuzzy_matched,
                        fuzzy_suggestions=fuzzy_suggestions,
                    )
        except Exception as e:
            pass

    fuzzy_suggestions = [s[0] for s in fuzzy_match_tool(text)]
    intent = "unknown"
    tool_name = ""
    params = {}
    confidence = 0.0
    explanation = f"No se pudo conectar al NLU principal. Se usó matching difuso."

    if fuzzy_suggestions:
        tool_name = fuzzy_suggestions[0]
        intent = (
            "query"
            if "get" in tool_name or "list" in tool_name or "search" in tool_name
            else "unknown"
        )
        confidence = (
            max(0.3, 1.0 - (fuzzy_match_tool(text)[0][1] / 10))
            if fuzzy_match_tool(text)
            else 0.3
        )
        explanation = f"Match difuso: '{text}' -> '{tool_name}'"

    _nlu_contexts[ctx_id].append(
        f"User: {text} -> Fuzzy: {tool_name} (intent: {intent})"
    )

    return NLUResponse(
        corrected_text=text,
        intent=intent,
        tool_name=tool_name,
        parameters=params,
        confidence=confidence,
        explanation=explanation,
        response=f"He interpretado tu comando como: {tool_name.replace('_', ' ')}"
        if tool_name
        else "No entendí el comando. Intenta ser más específico.",
        role=role,
        fuzzy_matched=bool(fuzzy_suggestions),
        fuzzy_suggestions=fuzzy_suggestions,
    )


@app.get("/mcp/fuzzy")
async def fuzzy_search(q: str = "", threshold: int = 3):
    if not q:
        return {"tools": TOOL_NAMES, "total": len(TOOL_NAMES)}
    matches = fuzzy_match_tool(q, threshold)
    return {
        "query": q,
        "matches": [{"name": name, "distance": dist} for name, dist in matches],
        "total": len(matches),
    }


# PROYECTOS
TOOLS["get_all_projects"] = {
    "function": projects.get_all_projects,
    "description": "Obtiene todos los proyectos",
    "params": {"limit": {"type": "integer", "default": 50}},
}
TOOLS["get_project_by_id"] = {
    "function": projects.get_project_by_id,
    "description": "Obtiene un proyecto por ID",
    "params": {"project_id": {"type": "integer", "required": True}},
}
TOOLS["search_projects"] = {
    "function": projects.search_projects,
    "description": "Busca proyectos",
    "params": {"query": {"type": "string", "required": True}},
}
TOOLS["analyze_project"] = {
    "function": projects.analyze_project_with_ai,
    "description": "Analiza proyecto con IA",
    "params": {"project_id": {"type": "integer", "required": True}},
}
TOOLS["generate_project_plan"] = {
    "function": projects.generate_project_plan,
    "description": "Genera plan de proyecto",
    "params": {
        "project_name": {"type": "string", "required": True},
        "tipo": {"type": "string", "required": True},
        "horas": {"type": "number", "required": True},
        "idioma": {"type": "string", "default": "Español"},
    },
}
TOOLS["get_projects_by_client"] = {
    "function": projects.get_projects_by_client,
    "description": "Proyectos por cliente",
    "params": {"client_id": {"type": "string", "required": True}},
}

# USUARIOS
TOOLS["get_all_users"] = {
    "function": users.get_all_users,
    "description": "Obtiene todos los usuarios",
    "params": {"limit": {"type": "integer", "default": 50}},
}
TOOLS["get_user_by_id"] = {
    "function": users.get_user_by_id,
    "description": "Obtiene usuario por ID",
    "params": {"user_id": {"type": "string", "required": True}},
}
TOOLS["search_users"] = {
    "function": users.search_users,
    "description": "Busca usuarios",
    "params": {"query": {"type": "string", "required": True}},
}
TOOLS["get_users_by_role"] = {
    "function": users.get_users_by_role,
    "description": "Usuarios por rol",
    "params": {"role_name": {"type": "string", "required": True}},
}
TOOLS["get_all_roles"] = {
    "function": users.get_all_roles,
    "description": "Todos los roles",
    "params": {},
}
TOOLS["get_role_permissions"] = {
    "function": users.get_role_permissions,
    "description": "Permisos de un rol",
    "params": {"role_id": {"type": "integer", "required": True}},
}

# CURSOS
TOOLS["get_all_courses"] = {
    "function": courses.get_all_courses,
    "description": "Todos los cursos",
    "params": {"limit": {"type": "integer", "default": 50}},
}
TOOLS["get_course_by_id"] = {
    "function": courses.get_course_by_id,
    "description": "Curso por ID",
    "params": {"course_id": {"type": "integer", "required": True}},
}
TOOLS["get_courses_by_project"] = {
    "function": courses.get_courses_by_project,
    "description": "Cursos por proyecto",
    "params": {"project_id": {"type": "integer", "required": True}},
}
TOOLS["generate_course_structure"] = {
    "function": courses.generate_course_structure,
    "description": "Genera estructura de curso",
    "params": {
        "course_name": {"type": "string", "required": True},
        "horas": {"type": "integer", "required": True},
        "idioma": {"type": "string", "default": "Español"},
        "publico": {"type": "string", "default": "General"},
    },
}
TOOLS["analyze_course_quality"] = {
    "function": courses.analyze_course_quality,
    "description": "Analiza calidad de curso",
    "params": {"course_id": {"type": "integer", "required": True}},
}

# TAREAS
TOOLS["get_tasks_by_project"] = {
    "function": tasks.get_tasks_by_project,
    "description": "Tareas de proyecto",
    "params": {"project_id": {"type": "integer", "required": True}},
}
TOOLS["get_task_by_id"] = {
    "function": tasks.get_task_by_id,
    "description": "Tarea por ID",
    "params": {"task_id": {"type": "integer", "required": True}},
}
TOOLS["get_tasks_by_user"] = {
    "function": tasks.get_tasks_by_user,
    "description": "Tareas de usuario",
    "params": {"user_id": {"type": "string", "required": True}},
}
TOOLS["get_pending_tasks"] = {
    "function": tasks.get_pending_tasks,
    "description": "Tareas pendientes",
    "params": {},
}
TOOLS["generate_task_suggestions"] = {
    "function": tasks.generate_task_suggestions,
    "description": "Sugerencias de tareas",
    "params": {
        "titulo": {"type": "string", "required": True},
        "descripcion": {"type": "string", "required": True},
        "complejidad": {"type": "string", "default": "media"},
    },
}
TOOLS["analyze_task_urgency"] = {
    "function": tasks.analyze_task_urgency,
    "description": "Analiza urgencia de tarea",
    "params": {"task_id": {"type": "integer", "required": True}},
}

# CLIENTES
TOOLS["get_all_clients"] = {
    "function": clients.get_all_clients,
    "description": "Todos los clientes",
    "params": {"limit": {"type": "integer", "default": 50}},
}
TOOLS["search_clients"] = {
    "function": clients.search_clients,
    "description": "Busca clientes por nombre, razón social o NIT",
    "params": {"query": {"type": "string", "required": True}},
}
TOOLS["get_client_by_id"] = {
    "function": clients.get_client_by_id,
    "description": "Cliente por ID",
    "params": {"client_id": {"type": "string", "required": True}},
}
TOOLS["get_clients_with_active_projects"] = {
    "function": clients.get_clients_with_active_projects,
    "description": "Clientes con proyectos activos",
    "params": {},
}
TOOLS["analyze_client"] = {
    "function": clients.analyze_client_with_ai,
    "description": "Analiza cliente con IA",
    "params": {"client_id": {"type": "string", "required": True}},
}

# CONTENIDO
TOOLS["get_all_documents"] = {
    "function": content.get_all_documents,
    "description": "Todos los documentos",
    "params": {"limit": {"type": "integer", "default": 50}},
}
TOOLS["get_documents_by_project"] = {
    "function": content.get_documents_by_project,
    "description": "Documentos por proyecto",
    "params": {"project_id": {"type": "integer", "required": True}},
}
TOOLS["get_fases"] = {
    "function": content.get_fases,
    "description": "Todas las fases",
    "params": {},
}
TOOLS["get_fase_by_id"] = {
    "function": content.get_fase_by_id,
    "description": "Fase por ID",
    "params": {"fase_id": {"type": "integer", "required": True}},
}
TOOLS["get_etapas"] = {
    "function": content.get_etapas,
    "description": "Todas las etapas",
    "params": {},
}
TOOLS["get_cronograma_by_project"] = {
    "function": content.get_cronograma_by_project,
    "description": "Cronograma por proyecto",
    "params": {"project_id": {"type": "integer", "required": True}},
}
TOOLS["get_modules_by_course"] = {
    "function": content.get_modules_by_course,
    "description": "Módulos por curso",
    "params": {"course_id": {"type": "integer", "required": True}},
}
TOOLS["get_units_by_module"] = {
    "function": content.get_units_by_module,
    "description": "Unidades por módulo",
    "params": {"module_id": {"type": "integer", "required": True}},
}

# ANALYTICS
TOOLS["get_dashboard_stats"] = {
    "function": analytics.get_dashboard_stats,
    "description": "Estadísticas del dashboard",
    "params": {},
}
TOOLS["get_projects_by_state"] = {
    "function": analytics.get_projects_by_state,
    "description": "Proyectos por estado",
    "params": {},
}
TOOLS["get_projects_by_type"] = {
    "function": analytics.get_projects_by_type,
    "description": "Proyectos por tipo",
    "params": {},
}
TOOLS["get_projects_timeline"] = {
    "function": analytics.get_projects_timeline,
    "description": "Línea de tiempo de proyectos",
    "params": {},
}
TOOLS["get_top_users_by_tasks"] = {
    "function": analytics.get_top_users_by_tasks,
    "description": "Usuarios con más tareas",
    "params": {},
}
TOOLS["generate_dashboard_report"] = {
    "function": analytics.generate_dashboard_report,
    "description": "Reporte de dashboard con IA",
    "params": {},
}

# CRUD PROYECTOS
TOOLS["create_project"] = {
    "function": projects.create_project,
    "description": "Crea un nuevo proyecto",
    "params": {
        "name": {"type": "string", "required": True},
        "client_id": {"type": "string", "required": True},
        "tipo_proyecto": {"type": "string", "required": True},
        "start_date": {
            "type": "string",
            "required": True,
            "description": "Fecha de inicio en formato YYYY-MM-DD",
        },
        "estado": {"type": "string", "default": "Planificado"},
        "description": {"type": "string", "default": ""},
        "idioma": {"type": "string", "default": "Español"},
        "end_date": {"type": "string", "default": ""},
        "etapa": {"type": "string", "default": "Etapa Contractual"},
    },
}
TOOLS["update_project"] = {
    "function": projects.update_project,
    "description": "Actualiza un proyecto",
    "params": {
        "project_id": {"type": "integer", "required": True},
        "name": {"type": "string", "default": None},
        "estado": {"type": "string", "default": None},
        "description": {"type": "string", "default": None},
        "start_date": {"type": "string", "default": None},
        "end_date": {"type": "string", "default": None},
        "etapa": {"type": "string", "default": None},
    },
}
TOOLS["delete_project"] = {
    "function": projects.delete_project,
    "description": "Elimina un proyecto",
    "params": {"project_id": {"type": "integer", "required": True}},
}

# CRUD USUARIOS
TOOLS["create_user"] = {
    "function": users.create_user,
    "description": "Crea un nuevo usuario",
    "params": {
        "email": {"type": "string", "required": True},
        "nombre": {"type": "string", "required": True},
        "password": {"type": "string", "default": None},
        "estado": {"type": "integer", "default": 1},
        "rol": {"type": "string", "default": "registrado"},
    },
}
TOOLS["update_user"] = {
    "function": users.update_user,
    "description": "Actualiza un usuario",
    "params": {
        "user_id": {"type": "string", "required": True},
        "email": {"type": "string", "default": None},
        "nombre": {"type": "string", "default": None},
        "estado": {"type": "integer", "default": None},
    },
}
TOOLS["delete_user"] = {
    "function": users.delete_user,
    "description": "Elimina un usuario",
    "params": {"user_id": {"type": "string", "required": True}},
}
TOOLS["assign_role"] = {
    "function": users.assign_role,
    "description": "Asigna rol a usuario",
    "params": {
        "user_id": {"type": "string", "required": True},
        "rol": {"type": "string", "required": True},
    },
}

# CRUD CLIENTES
TOOLS["create_client"] = {
    "function": clients.create_client,
    "description": "Crea un nuevo cliente",
    "params": {
        "razon_social": {"type": "string", "required": True},
        "nit": {"type": "string", "default": ""},
        "user_id": {"type": "string", "default": None},
        "tipo_entidad": {"type": "string", "default": "Privada"},
        "direccion": {"type": "string", "default": ""},
        "ciudad": {"type": "string", "default": ""},
        "pais": {"type": "string", "default": "Colombia"},
    },
}
TOOLS["update_client"] = {
    "function": clients.update_client,
    "description": "Actualiza un cliente",
    "params": {
        "client_id": {"type": "string", "required": True},
        "razon_social": {"type": "string", "default": None},
        "nit": {"type": "string", "default": None},
        "tipo_entidad": {"type": "string", "default": None},
        "direccion": {"type": "string", "default": None},
        "ciudad": {"type": "string", "default": None},
        "pais": {"type": "string", "default": None},
    },
}
TOOLS["delete_client"] = {
    "function": clients.delete_client,
    "description": "Elimina un cliente",
    "params": {"client_id": {"type": "string", "required": True}},
}


# PARTICIPANTES
def _add_participant_wrapper(
    project_id: int,
    user_id: str = None,
    user_uid: str = None,
    role_id: int = 1,
    user_name: str = None,
    project_name: str = None,
):
    """Wrapper that accepts user_id (resolved from user_name) and maps to user_uid."""
    uid = user_uid or user_id or ""
    return projects.add_participant(project_id, uid, role_id)


TOOLS["add_participant"] = {
    "function": _add_participant_wrapper,
    "description": "Agrega un participante a un proyecto. Usa 'user_name' (nombre de usuario) en vez de user_uid.",
    "params": {
        "project_id": {"type": "integer", "required": True},
        "user_id": {
            "type": "string",
            "required": True,
            "description": "UUID del usuario (se resuelve automáticamente desde user_name)",
        },
        "role_id": {"type": "integer", "default": 1},
    },
}
TOOLS["get_participants"] = {
    "function": projects.get_participants,
    "description": "Obtiene participantes de un proyecto",
    "params": {"project_id": {"type": "integer", "required": True}},
}

# CRUD TAREAS
TOOLS["create_task"] = {
    "function": tasks.create_task,
    "description": "Crea una nueva tarea",
    "params": {
        "titulo": {"type": "string", "required": True},
        "project_id": {"type": "integer", "required": True},
        "descripcion": {"type": "string", "default": ""},
        "asignado_a": {"type": "string", "default": None},
        "prioridad": {"type": "string", "default": "media"},
        "estado": {"type": "string", "default": "pendiente"},
        "fecha_entrega": {"type": "string", "default": None},
    },
}
TOOLS["update_task"] = {
    "function": tasks.update_task,
    "description": "Actualiza una tarea",
    "params": {
        "task_id": {"type": "integer", "required": True},
        "titulo": {"type": "string", "default": None},
        "descripcion": {"type": "string", "default": None},
        "prioridad": {"type": "string", "default": None},
        "estado": {"type": "string", "default": None},
        "fecha_entrega": {"type": "string", "default": None},
        "asignado_a": {"type": "string", "default": None},
    },
}
TOOLS["delete_task"] = {
    "function": tasks.delete_task,
    "description": "Elimina una tarea",
    "params": {"task_id": {"type": "integer", "required": True}},
}
TOOLS["complete_task"] = {
    "function": tasks.complete_task,
    "description": "Marca tarea como completada",
    "params": {"task_id": {"type": "integer", "required": True}},
}
TOOLS["get_task_stats"] = {
    "function": tasks.get_task_stats,
    "description": "Estadísticas de tareas",
    "params": {},
}

TOOL_NAMES = sorted(TOOLS.keys())

# === CHAT CONVERSACIONAL MULTI-TURNO ===

from dataclasses import dataclass, field
from fastapi import WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types as gemini_types


@dataclass
class SessionState:
    tool_name: str = ""
    params: dict = field(default_factory=dict)
    missing: list = field(default_factory=list)
    history: list = field(default_factory=list)
    status: str = "idle"  # idle | collecting | confirming | executing | planning
    token: str = ""
    resolved_ids: dict = field(default_factory=dict)
    memory: MemoryContext = field(default_factory=MemoryContext)
    plan_awaiting_confirmation: bool = False


_sessions: dict[str, SessionState] = {}

_gemini_clients: list = []
_gemini_key_index = 0

# Pool de API keys desde variable de entorno (separadas por coma)
GEMINI_API_KEYS = [
    k.strip() for k in os.environ.get("GEMINI_API_KEYS", "").split(",") if k.strip()
]


def _get_client():
    global _gemini_clients, _gemini_key_index
    if not _gemini_clients:
        for key in GEMINI_API_KEYS:
            if key:
                try:
                    _gemini_clients.append(genai.Client(api_key=key))
                except Exception:
                    pass
    if not _gemini_clients:
        return None
    client = _gemini_clients[_gemini_key_index % len(_gemini_clients)]
    _gemini_key_index += 1
    return client


def _build_tools_schema() -> str:
    lines = []
    for name, tool in TOOLS.items():
        req = [k for k, v in tool["params"].items() if v.get("required")]
        opt = [k for k, v in tool["params"].items() if not v.get("required")]
        lines.append(f"- {name}: {tool['description']}")
        if req:
            lines.append(f"  REQUERIDOS: {', '.join(req)}")
        if opt:
            lines.append(f"  OPCIONALES: {', '.join(opt)}")
    return "\n".join(lines)


def _build_system_prompt(session: SessionState) -> str:
    base = PLANNING_SYSTEM_PROMPT
    context = session.memory.get_context_prompt()
    if context:
        base += f"\n\nCONTEXTO DE LA SESIÓN:\n{context}\n"
    base += f"\n\nHERRAMIENTAS DISPONIBLES:\n{_build_tools_schema()}\n"
    return base


def _build_history(session: SessionState) -> list:
    msgs = []
    for h in session.history:
        msgs.append(
            gemini_types.Content(
                role=h["role"], parts=[gemini_types.Part(text=h["text"])]
            )
        )
    return msgs


async def _ask_gemini(session: SessionState, user_text: str) -> str:
    client = _get_client()
    if not client:
        return "⛔ Gemini no configurado (falta GEMINI_API_KEY)"

    session.history.append({"role": "user", "text": user_text})

    contents = _build_history(session)
    system_prompt = _build_system_prompt(session)
    config = gemini_types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.3,
        max_output_tokens=2048,
    )

    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config=config,
        )
        text = response.text.strip()
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            client = _get_client()
            if client:
                try:
                    response = await client.aio.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=contents,
                        config=config,
                    )
                    text = response.text.strip()
                except Exception as e2:
                    text = f"⚠️ Error (sin quota): {str(e2)[:200]}"
            else:
                text = f"⚠️ Error: {err_str[:200]}"
        else:
            text = f"⚠️ Error: {err_str[:200]}"

    session.history.append({"role": "model", "text": text})
    return text


async def _ask_gemini_raw(session: SessionState) -> str:
    """Ask Gemini without adding a user message (used after tool results)."""
    client = _get_client()
    if not client:
        return "⛔ Gemini no configurado"

    contents = _build_history(session)
    system_prompt = _build_system_prompt(session)
    config = gemini_types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.3,
        max_output_tokens=2048,
    )

    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config=config,
        )
        text = response.text.strip()
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            client = _get_client()
            if client:
                try:
                    response = await client.aio.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=contents,
                        config=config,
                    )
                    text = response.text.strip()
                except Exception as e2:
                    text = f"⚠️ Error (sin quota): {str(e2)[:200]}"
            else:
                text = f"⚠️ Error: {err_str[:200]}"
        else:
            text = f"⚠️ Error: {err_str[:200]}"

    session.history.append({"role": "model", "text": text})
    return text


async def _call_any_tool(tool_name: str, params: dict, token: str = "") -> dict:
    """Execute any registered tool (for mid-conversation lookups)."""
    if token and tool_name in API_BRIDGE_MAP:
        try:
            from app.colmena.api_bridge import ApiBridge

            bridge = ApiBridge(token)
            bridge_info = API_BRIDGE_MAP[tool_name]
            method_name = bridge_info[0]
            method = getattr(bridge, method_name)
            if len(bridge_info) >= 3:
                id_param = bridge_info[2]
                id_value = params.pop(id_param, None)
                if id_value is not None:
                    result = await method(id_value, **params)
                else:
                    result = await method(**params)
            else:
                result = await method(**params)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    if tool_name in TOOLS:
        try:
            func = TOOLS[tool_name]["function"]
            result = func(**params)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Tool '{tool_name}' no encontrada"}


async def _resolve_entity_names(params: dict) -> dict:
    """Resuelve nombres de entidades a IDs automáticamente."""
    resolved = dict(params)

    name_to_id_fields = {
        "client_name": ("search_clients", "query", "user_id"),
        "project_name": ("search_projects", "query", "id"),
        "user_name": ("search_users", "query", "uid"),
    }

    for name_field, (tool, search_param, id_field) in name_to_id_fields.items():
        if name_field in resolved and resolved[name_field]:
            name = resolved.pop(name_field)
            id_field_name = name_field.replace("_name", "_id")
            try:
                if tool in TOOLS:
                    func = TOOLS[tool]["function"]
                    results = func(**{search_param: name})
                    if results and isinstance(results, list) and len(results) > 0:
                        first = results[0]
                        if isinstance(first, dict):
                            resolved[id_field_name] = str(
                                first.get(id_field, first.get("id", ""))
                            )
                            # Also set user_uid if this resolved from user_name (for assign_participant)
                            if id_field == "uid" and "user_uid" not in resolved:
                                resolved["user_uid"] = str(
                                    first.get("uid", first.get(id_field, ""))
                                )
                            # Also set razon_social/name for ${ref} resolution
                            if "razon_social" in first:
                                resolved["_razon_social"] = first["razon_social"]
                            if "nombre" in first:
                                resolved["_nombre"] = first["nombre"]
                        elif hasattr(first, "_mapping"):
                            resolved[id_field_name] = str(
                                first._mapping.get(id_field, "")
                            )
            except Exception:
                pass

    return resolved


async def _try_execute(session: SessionState, response: str) -> dict | None:
    if not response.startswith("##EXECUTE##"):
        return None
    parts = response.replace("##EXECUTE##", "").strip().split("|")
    tool_name = parts[0].strip()
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.strip()] = v.strip()
    # Merge with already collected params
    params = {**session.params, **params}
    # Resolve entity names to IDs automatically
    params = await _resolve_entity_names(params)

    session.status = "executing"
    token = session.token
    # Try bridge first, then local
    if token and tool_name in API_BRIDGE_MAP:
        try:
            from app.colmena.api_bridge import ApiBridge

            bridge = ApiBridge(token)
            bridge_info = API_BRIDGE_MAP[tool_name]
            method_name = bridge_info[0]
            method = getattr(bridge, method_name)
            if len(bridge_info) >= 3:
                id_param = bridge_info[2]
                id_value = params.pop(id_param, None)
                if id_value is not None:
                    result = await method(id_value, **params)
                else:
                    result = await method(**params)
            else:
                result = await method(**params)
            return {"status": "success", "tool": tool_name, "result": result}
        except Exception as e:
            return {"status": "error", "tool": tool_name, "error": str(e)}

    if tool_name in TOOLS:
        try:
            func = TOOLS[tool_name]["function"]
            result = func(**params)
            return {"status": "success", "tool": tool_name, "result": result}
        except Exception as e:
            return {"status": "error", "tool": tool_name, "error": str(e)}

    return {
        "status": "error",
        "tool": tool_name,
        "error": f"Tool '{tool_name}' no encontrada",
    }


@app.websocket("/mcp/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if session_id not in _sessions:
        _sessions[session_id] = SessionState()
    session = _sessions[session_id]
    session.status = "idle"
    token = websocket.query_params.get("token", "")
    if token:
        session.token = token

    await websocket.send_text(
        json.dumps(
            {
                "type": "info",
                "message": "🐝 Conectado al MCP Conversacional. ¿En qué puedo ayudarte?",
            }
        )
    )

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            user_msg = data.get("text", "").strip()
            reset = data.get("reset", False)

            if reset:
                _sessions[session_id] = SessionState()
                session = _sessions[session_id]
                await websocket.send_text(
                    json.dumps({"type": "info", "message": "🔄 Sesión reiniciada"})
                )
                continue

            if not user_msg:
                continue

            response = await _ask_gemini(session, user_msg)

            # Process loop: handle ##PLAN##, ##TOOL##, and ##EXECUTE##
            max_iter = 5
            for _ in range(max_iter):
                print(f"[DEBUG] Gemini response: {response[:300]}", flush=True)

                chat_prefix = ""
                for cmd in ["##PLAN##", "##TOOL##", "##EXECUTE##"]:
                    idx = response.find(cmd)
                    if idx > 0:
                        chat_prefix = response[:idx].strip()
                        response = response[idx:]
                        break
                    elif idx == 0:
                        chat_prefix = ""

                # Check for multi-step plan
                if "##PLAN##" in response:
                    if chat_prefix:
                        await websocket.send_text(
                            json.dumps({"type": "chat", "message": chat_prefix})
                        )

                    orchestrator = AgentOrchestrator(
                        session=session,
                        memory=session.memory,
                        call_tool_fn=lambda tn, p: _call_any_tool(tn, p, session.token),
                        resolve_names_fn=_resolve_entity_names,
                    )

                    plan = await orchestrator.create_plan(response)
                    if plan:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "plan_start",
                                    "steps": [
                                        {
                                            "tool": s.tool_name,
                                            "description": s.description,
                                            "id": s.id,
                                        }
                                        for s in plan.steps
                                    ],
                                    "total": len(plan.steps),
                                    "parallel_groups": len(plan.parallel_groups),
                                }
                            )
                        )

                        plan = await orchestrator.execute_plan(plan)

                        # Send individual step results
                        for step in plan.steps:
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "step_result",
                                        "id": step.id,
                                        "tool": step.tool_name,
                                        "status": step.status,
                                        "result": step.result
                                        if step.status == "success"
                                        else None,
                                        "error": step.error
                                        if step.status == "failed"
                                        else None,
                                    }
                                )
                            )

                        # Build a summary for Gemini
                        summary_lines = []
                        for step in plan.steps:
                            status_icon = (
                                "✅"
                                if step.status == "success"
                                else "❌"
                                if step.status == "failed"
                                else "⏭️"
                            )
                            summary_lines.append(
                                f"{status_icon} Paso {step.id}: {step.tool_name} -> {step.status}"
                            )
                            if step.status == "success" and step.result:
                                summary_lines.append(
                                    f"   Resultado: {json.dumps(step.result, ensure_ascii=False)[:300]}"
                                )
                            if step.status == "failed" and step.error:
                                summary_lines.append(f"   Error: {step.error}")

                        session.history.append(
                            {
                                "role": "user",
                                "text": f"[Plan ejecutado. Resumen:\n"
                                + "\n".join(summary_lines)
                                + "\n] "
                                f"Informa al usuario del resultado de forma clara y natural.",
                            }
                        )

                        response = await _ask_gemini_raw(session)
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "chat",
                                    "message": response,
                                }
                            )
                        )
                        session.status = "idle"
                        break
                    else:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "No pude interpretar el plan. Intenta de nuevo.",
                                }
                            )
                        )
                        break

                # Check for mid-conversation tool call (lookup)
                tool_match = re.search(
                    r"##TOOL##\s+(\w+)\s*\|\s*(.*)", response, re.DOTALL
                )
                if tool_match:
                    tool_name = tool_match.group(1)
                    raw_params = tool_match.group(2).strip()
                    tool_params = {}
                    for p in raw_params.split("|"):
                        if "=" in p:
                            k, v = p.split("=", 1)
                            tool_params[k.strip()] = v.strip()

                    if chat_prefix:
                        await websocket.send_text(
                            json.dumps({"type": "chat", "message": chat_prefix})
                        )

                    tool_result = await _call_any_tool(
                        tool_name, tool_params, session.token
                    )
                    result_str = json.dumps(tool_result, ensure_ascii=False)[:2000]

                    session.history.append(
                        {
                            "role": "user",
                            "text": f"[Resultado de {tool_name}: {result_str}] Sigue la conversación naturalmente. "
                            f"Si encontraste lo que buscabas, informa al usuario y continúa preguntando.",
                        }
                    )

                    response = await _ask_gemini_raw(session)
                    continue

                # Check for single-tool execution
                exec_result = await _try_execute(session, response)
                if exec_result:
                    if chat_prefix:
                        await websocket.send_text(
                            json.dumps({"type": "chat", "message": chat_prefix})
                        )
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "execution",
                                "tool": exec_result["tool"],
                                "status": exec_result["status"],
                                "result": exec_result.get("result"),
                                "error": exec_result.get("error"),
                            }
                        )
                    )

                    # Track entity in memory
                    if exec_result.get("status") == "success":
                        result_data = exec_result.get("result", {})
                        if isinstance(result_data, dict):
                            if result_data.get("project_id"):
                                session.memory.track_entity(
                                    "projects",
                                    {
                                        "id": result_data["project_id"],
                                        "name": result_data.get("message", ""),
                                    },
                                )

                    session.status = "idle"
                    break

                # Normal chat response
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "chat",
                            "message": chat_prefix
                            + ("\n\n" + response if chat_prefix else response),
                        }
                    )
                )
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass


@app.get("/")
def root():
    return {
        "name": "VirtualMind MCP Server",
        "version": "1.0.0",
        "status": "running",
        "tools_count": len(TOOLS),
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/config")
def get_config():
    return {
        "gemini_api_keys": GEMINI_API_KEYS,
        "model": "gemini-2.5-flash-lite",
        "tools_count": len(TOOLS),
    }


@app.get("/tools")
def list_tools():
    tools_list = []
    for name, tool in TOOLS.items():
        tools_list.append(
            {"name": name, "description": tool["description"], "params": tool["params"]}
        )
    return {"tools": tools_list, "total": len(TOOLS)}


@app.post("/mcp/tools")
async def call_tool(request: ToolRequest):
    tool_name = request.tool_name
    params = request.params or {}
    token = request.token

    if tool_name not in TOOLS:
        return {
            "error": f"Tool '{tool_name}' no encontrada",
            "available_tools": list(TOOLS.keys()),
        }

    if token and tool_name in API_BRIDGE_MAP:
        try:
            from app.colmena.api_bridge import ApiBridge

            bridge = ApiBridge(token)
            bridge_info = API_BRIDGE_MAP[tool_name]
            if isinstance(bridge_info, str):
                method = getattr(bridge, bridge_info)
                result = await method(**params)
            else:
                method_name = bridge_info[0]
                method = getattr(bridge, method_name)
                if len(bridge_info) >= 3:
                    id_param = bridge_info[2]
                    id_value = params.pop(id_param, None)
                    if id_value is not None:
                        result = await method(id_value, **params)
                    else:
                        result = await method(**params)
                else:
                    result = await method(**params)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    tool = TOOLS[tool_name]
    func = tool["function"]
    try:
        result = func(**params)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = "gemini-2.5-flash-lite"
    temperature: float = 0.7
    max_tokens: int = 4096
    system: Optional[str] = None


async def generate_stream(request: GenerateRequest):
    """Genera contenido usando Gemini con streaming SSE"""
    try:
        from google import genai
        from google.genai import types

        client = _get_client()
        if not client:
            yield {
                "event": "error",
                "data": json.dumps({"error": "No hay API keys de Gemini disponibles"}),
            }
            return

        config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            system_instruction=request.system,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[request.prompt],
            config=config,
        )

        text = response.text
        if text:
            words = text.split()
            for i, word in enumerate(words):
                yield {
                    "event": "message",
                    "data": json.dumps(
                        {"response": word + " ", "model": request.model}
                    ),
                }
                await asyncio.sleep(0.05)

        yield {"event": "done", "data": json.dumps({"model": request.model})}

    except Exception as e:
        yield {"event": "error", "data": json.dumps({"error": str(e)})}


@app.get("/generate/stream")
async def generate_stream_get(request: Request):
    """Endpoint SSE para generación de texto"""
    prompt = request.query_params.get("prompt", "")
    model = request.query_params.get("model", "gemini-2.5-flash-lite")
    temperature = float(request.query_params.get("temperature", 0.7))
    max_tokens = int(request.query_params.get("max_tokens", 4096))
    system = request.query_params.get("system", None)

    req = GenerateRequest(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        system=system,
    )
    return EventSourceResponse(generate_stream(req))


@app.post("/generate/stream")
async def generate_stream_post(request: GenerateRequest):
    """Endpoint SSE para generación de texto (POST)"""
    return EventSourceResponse(generate_stream(request))


@app.get("/chat/stream")
async def chat_stream_get(request: Request):
    """Endpoint SSE para chat con Gemini"""
    prompt = request.query_params.get("prompt", "")
    model = request.query_params.get("model", "gemini-2.5-flash-lite")
    temperature = float(request.query_params.get("temperature", 0.7))
    max_tokens = int(request.query_params.get("max_tokens", 4096))

    req = GenerateRequest(
        prompt=prompt, model=model, temperature=temperature, max_tokens=max_tokens
    )
    return EventSourceResponse(generate_stream(req))


@app.post("/chat/stream")
async def chat_stream_post(request: GenerateRequest):
    """Endpoint SSE para chat (POST)"""
    return EventSourceResponse(generate_stream(request))


@app.get("/sse")
async def sse(request: Request):
    """Endpoint SSE para mantener conexión"""

    async def event_generator():
        while True:
            yield {
                "event": "ping",
                "data": json.dumps({"time": datetime.now().isoformat()}),
            }
            await asyncio.sleep(30)

    return EventSourceResponse(event_generator())


@app.post("/messages")
async def handle_message(request: Request):
    """Maneja mensajes entrantes del cliente MCP"""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})

        if method == "generate" or method == "chat":
            req = GenerateRequest(**params)
            return EventSourceResponse(generate_stream(req))
        elif method == "list_tools":
            tools = list_tools()
            return tools
        elif method == "call_tool":
            return await call_tool(ToolRequest(**params))
        elif method == "health":
            return health_check()
        else:
            return {"error": f"Método '{method}' no soportado"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    import ssl

    ssl_cert = "/etc/letsencrypt/live/gestordecursos.pegui.edu.co/fullchain.pem"
    ssl_key = "/etc/letsencrypt/live/gestordecursos.pegui.edu.co/privkey.pem"

    uvicorn.run(
        app, host="0.0.0.0", port=8001, ssl_keyfile=ssl_key, ssl_certfile=ssl_cert
    )
