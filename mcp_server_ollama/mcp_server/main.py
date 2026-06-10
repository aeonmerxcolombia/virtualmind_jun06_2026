"""
MCP Server para VirtualMind
Expone herramientas de IA conectadas a la base de datos
"""

import sys
sys.path.insert(0, '/home/ubuntu/backend')

import json
import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from sse_starlette.sse import EventSourceResponse

from mcp_server.tools import projects, users, courses, tasks, clients, content, analytics
from mcp_server.tools.ai import generate_with_ai

app = FastAPI(
    title="VirtualMind MCP Server",
    description="Servidor MCP con herramientas de IA para VirtualMind",
    version="1.1.0"
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

TOOLS: Dict[str, Any] = {}

# PROYECTOS
TOOLS["get_all_projects"] = {
    "function": projects.get_all_projects,
    "description": "Obtiene todos los proyectos",
    "params": {"limit": {"type": "integer", "default": 50}}
}
TOOLS["get_project_by_id"] = {
    "function": projects.get_project_by_id,
    "description": "Obtiene un proyecto por ID",
    "params": {"project_id": {"type": "integer", "required": True}}
}
TOOLS["search_projects"] = {
    "function": projects.search_projects,
    "description": "Busca proyectos",
    "params": {"query": {"type": "string", "required": True}}
}
TOOLS["analyze_project"] = {
    "function": projects.analyze_project_with_ai,
    "description": "Analiza proyecto con IA",
    "params": {"project_id": {"type": "integer", "required": True}}
}
TOOLS["generate_project_plan"] = {
    "function": projects.generate_project_plan,
    "description": "Genera plan de proyecto",
    "params": {
        "project_name": {"type": "string", "required": True},
        "tipo": {"type": "string", "required": True},
        "horas": {"type": "number", "required": True},
        "idioma": {"type": "string", "default": "Español"}
    }
}
TOOLS["get_projects_by_client"] = {
    "function": projects.get_projects_by_client,
    "description": "Proyectos por cliente",
    "params": {"client_id": {"type": "string", "required": True}}
}

# USUARIOS
TOOLS["get_all_users"] = {
    "function": users.get_all_users,
    "description": "Obtiene todos los usuarios",
    "params": {"limit": {"type": "integer", "default": 50}}
}
TOOLS["get_user_by_id"] = {
    "function": users.get_user_by_id,
    "description": "Obtiene usuario por ID",
    "params": {"user_id": {"type": "string", "required": True}}
}
TOOLS["search_users"] = {
    "function": users.search_users,
    "description": "Busca usuarios",
    "params": {"query": {"type": "string", "required": True}}
}
TOOLS["get_users_by_role"] = {
    "function": users.get_users_by_role,
    "description": "Usuarios por rol",
    "params": {"role_name": {"type": "string", "required": True}}
}
TOOLS["get_all_roles"] = {
    "function": users.get_all_roles,
    "description": "Todos los roles",
    "params": {}
}
TOOLS["get_role_permissions"] = {
    "function": users.get_role_permissions,
    "description": "Permisos de un rol",
    "params": {"role_id": {"type": "integer", "required": True}}
}

# CURSOS
TOOLS["get_all_courses"] = {
    "function": courses.get_all_courses,
    "description": "Todos los cursos",
    "params": {"limit": {"type": "integer", "default": 50}}
}
TOOLS["get_course_by_id"] = {
    "function": courses.get_course_by_id,
    "description": "Curso por ID",
    "params": {"course_id": {"type": "integer", "required": True}}
}
TOOLS["get_courses_by_project"] = {
    "function": courses.get_courses_by_project,
    "description": "Cursos por proyecto",
    "params": {"project_id": {"type": "integer", "required": True}}
}
TOOLS["generate_course_structure"] = {
    "function": courses.generate_course_structure,
    "description": "Genera estructura de curso",
    "params": {
        "course_name": {"type": "string", "required": True},
        "horas": {"type": "integer", "required": True},
        "idioma": {"type": "string", "default": "Español"},
        "publico": {"type": "string", "default": "General"}
    }
}
TOOLS["analyze_course_quality"] = {
    "function": courses.analyze_course_quality,
    "description": "Analiza calidad de curso",
    "params": {"course_id": {"type": "integer", "required": True}}
}

# TAREAS
TOOLS["get_tasks_by_project"] = {
    "function": tasks.get_tasks_by_project,
    "description": "Tareas de proyecto",
    "params": {"project_id": {"type": "integer", "required": True}}
}
TOOLS["get_task_by_id"] = {
    "function": tasks.get_task_by_id,
    "description": "Tarea por ID",
    "params": {"task_id": {"type": "integer", "required": True}}
}
TOOLS["get_tasks_by_user"] = {
    "function": tasks.get_tasks_by_user,
    "description": "Tareas de usuario",
    "params": {"user_id": {"type": "string", "required": True}}
}
TOOLS["get_pending_tasks"] = {
    "function": tasks.get_pending_tasks,
    "description": "Tareas pendientes",
    "params": {}
}
TOOLS["generate_task_suggestions"] = {
    "function": tasks.generate_task_suggestions,
    "description": "Sugerencias de tareas",
    "params": {
        "titulo": {"type": "string", "required": True},
        "descripcion": {"type": "string", "required": True},
        "complejidad": {"type": "string", "default": "media"}
    }
}
TOOLS["analyze_task_urgency"] = {
    "function": tasks.analyze_task_urgency,
    "description": "Analiza urgencia de tarea",
    "params": {"task_id": {"type": "integer", "required": True}}
}

# CLIENTES
TOOLS["get_all_clients"] = {
    "function": clients.get_all_clients,
    "description": "Todos los clientes",
    "params": {"limit": {"type": "integer", "default": 50}}
}
TOOLS["get_client_by_id"] = {
    "function": clients.get_client_by_id,
    "description": "Cliente por ID",
    "params": {"client_id": {"type": "string", "required": True}}
}
TOOLS["get_clients_with_active_projects"] = {
    "function": clients.get_clients_with_active_projects,
    "description": "Clientes con proyectos activos",
    "params": {}
}
TOOLS["analyze_client"] = {
    "function": clients.analyze_client_with_ai,
    "description": "Analiza cliente con IA",
    "params": {"client_id": {"type": "string", "required": True}}
}

# CONTENIDO
TOOLS["get_all_documents"] = {
    "function": content.get_all_documents,
    "description": "Todos los documentos",
    "params": {"limit": {"type": "integer", "default": 50}}
}
TOOLS["get_documents_by_project"] = {
    "function": content.get_documents_by_project,
    "description": "Documentos por proyecto",
    "params": {"project_id": {"type": "integer", "required": True}}
}
TOOLS["get_fases"] = {
    "function": content.get_fases,
    "description": "Todas las fases",
    "params": {}
}
TOOLS["get_fase_by_id"] = {
    "function": content.get_fase_by_id,
    "description": "Fase por ID",
    "params": {"fase_id": {"type": "integer", "required": True}}
}
TOOLS["get_etapas"] = {
    "function": content.get_etapas,
    "description": "Todas las etapas",
    "params": {}
}
TOOLS["get_cronograma_by_project"] = {
    "function": content.get_cronograma_by_project,
    "description": "Cronograma por proyecto",
    "params": {"project_id": {"type": "integer", "required": True}}
}
TOOLS["get_modules_by_course"] = {
    "function": content.get_modules_by_course,
    "description": "Módulos por curso",
    "params": {"course_id": {"type": "integer", "required": True}}
}
TOOLS["get_units_by_module"] = {
    "function": content.get_units_by_module,
    "description": "Unidades por módulo",
    "params": {"module_id": {"type": "integer", "required": True}}
}

# ANALYTICS
TOOLS["get_dashboard_stats"] = {
    "function": analytics.get_dashboard_stats,
    "description": "Estadísticas del dashboard",
    "params": {}
}
TOOLS["get_projects_by_state"] = {
    "function": analytics.get_projects_by_state,
    "description": "Proyectos por estado",
    "params": {}
}
TOOLS["get_projects_by_type"] = {
    "function": analytics.get_projects_by_type,
    "description": "Proyectos por tipo",
    "params": {}
}
TOOLS["get_projects_timeline"] = {
    "function": analytics.get_projects_timeline,
    "description": "Línea de tiempo de proyectos",
    "params": {}
}
TOOLS["get_top_users_by_tasks"] = {
    "function": analytics.get_top_users_by_tasks,
    "description": "Usuarios con más tareas",
    "params": {}
}
TOOLS["generate_dashboard_report"] = {
    "function": analytics.generate_dashboard_report,
    "description": "Reporte de dashboard con IA",
    "params": {}
}

# CRUD PROYECTOS
TOOLS["create_project"] = {
    "function": projects.create_project,
    "description": "Crea un nuevo proyecto",
    "params": {
        "name": {"type": "string", "required": True},
        "client_id": {"type": "string", "required": True},
        "tipo_proyecto": {"type": "string", "required": True},
        "estado": {"type": "string", "default": "Planificado"},
        "description": {"type": "string", "default": ""},
        "idioma": {"type": "string", "default": "Español"},
        "start_date": {"type": "string", "default": None},
        "end_date": {"type": "string", "default": None},
        "etapa": {"type": "string", "default": "Etapa Contractual"}
    }
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
        "etapa": {"type": "string", "default": None}
    }
}
TOOLS["delete_project"] = {
    "function": projects.delete_project,
    "description": "Elimina un proyecto",
    "params": {"project_id": {"type": "integer", "required": True}}
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
        "rol": {"type": "string", "default": "registrado"}
    }
}
TOOLS["update_user"] = {
    "function": users.update_user,
    "description": "Actualiza un usuario",
    "params": {
        "user_id": {"type": "string", "required": True},
        "email": {"type": "string", "default": None},
        "nombre": {"type": "string", "default": None},
        "estado": {"type": "integer", "default": None}
    }
}
TOOLS["delete_user"] = {
    "function": users.delete_user,
    "description": "Elimina un usuario",
    "params": {"user_id": {"type": "string", "required": True}}
}
TOOLS["assign_role"] = {
    "function": users.assign_role,
    "description": "Asigna rol a usuario",
    "params": {
        "user_id": {"type": "string", "required": True},
        "rol": {"type": "string", "required": True}
    }
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
        "pais": {"type": "string", "default": "Colombia"}
    }
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
        "pais": {"type": "string", "default": None}
    }
}
TOOLS["delete_client"] = {
    "function": clients.delete_client,
    "description": "Elimina un cliente",
    "params": {"client_id": {"type": "string", "required": True}}
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
        "fecha_entrega": {"type": "string", "default": None}
    }
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
        "asignado_a": {"type": "string", "default": None}
    }
}
TOOLS["delete_task"] = {
    "function": tasks.delete_task,
    "description": "Elimina una tarea",
    "params": {"task_id": {"type": "integer", "required": True}}
}
TOOLS["complete_task"] = {
    "function": tasks.complete_task,
    "description": "Marca tarea como completada",
    "params": {"task_id": {"type": "integer", "required": True}}
}
TOOLS["get_task_stats"] = {
    "function": tasks.get_task_stats,
    "description": "Estadísticas de tareas",
    "params": {}
}

@app.get("/")
def root():
    return {
        "name": "VirtualMind MCP Server",
        "version": "1.0.0",
        "status": "running",
        "tools_count": len(TOOLS)
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/tools")
def list_tools():
    tools_list = []
    for name, tool in TOOLS.items():
        tools_list.append({
            "name": name,
            "description": tool["description"],
            "params": tool["params"]
        })
    return {"tools": tools_list, "total": len(TOOLS)}

@app.post("/mcp/tools")
def call_tool(request: ToolRequest):
    tool_name = request.tool_name
    params = request.params or {}
    
    if tool_name not in TOOLS:
        return {"error": f"Tool '{tool_name}' no encontrada", "available_tools": list(TOOLS.keys())}
    
    tool = TOOLS[tool_name]
    func = tool["function"]
    
    try:
        result = func(**params)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = "gemini-2.5-flash"
    temperature: float = 0.7
    max_tokens: int = 4096
    system: Optional[str] = None

async def generate_stream(request: GenerateRequest):
    """Genera contenido usando Gemini con streaming SSE"""
    try:
        from google import genai
        from google.genai import types
        
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        if not GEMINI_API_KEY:
            yield {"event": "error", "data": json.dumps({"error": "GEMINI_API_KEY no configurada"})}
            return
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            system_instruction=request.system,
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[request.prompt],
            config=config,
        )
        
        text = response.text
        if text:
            words = text.split()
            for i, word in enumerate(words):
                yield {"event": "message", "data": json.dumps({"response": word + " ", "model": request.model})}
                await asyncio.sleep(0.05)
        
        yield {"event": "done", "data": json.dumps({"model": request.model})}
        
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"error": str(e)})}

@app.get("/generate/stream")
async def generate_stream_get(request: Request):
    """Endpoint SSE para generación de texto"""
    prompt = request.query_params.get("prompt", "")
    model = request.query_params.get("model", "gemini-2.5-flash")
    temperature = float(request.query_params.get("temperature", 0.7))
    max_tokens = int(request.query_params.get("max_tokens", 4096))
    system = request.query_params.get("system", None)
    
    req = GenerateRequest(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        system=system
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
    model = request.query_params.get("model", "gemini-2.5-flash")
    temperature = float(request.query_params.get("temperature", 0.7))
    max_tokens = int(request.query_params.get("max_tokens", 4096))
    
    req = GenerateRequest(prompt=prompt, model=model, temperature=temperature, max_tokens=max_tokens)
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
            yield {"event": "ping", "data": json.dumps({"time": datetime.now().isoformat()})}
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
            return call_tool(ToolRequest(**params))
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
        app, 
        host="0.0.0.0", 
        port=8001,
        ssl_keyfile=ssl_key,
        ssl_certfile=ssl_cert
    )
