"""
Colmena Tools — Herramientas granulares que llaman la API real via ApiBridge.
Cada tool tiene descripciones claras de campos requeridos/opcionales.
Soporta flujo paso a paso: si faltan campos, la API devuelve error 422 con detalle,
y el AgentBrain le pide al usuario lo que falta.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from app.colmena.api_bridge import ApiBridge, ApiBridgeError

logger = logging.getLogger("colmena.tools")

TOOL_META = {
    "category": "",
    "required_roles": [],
    "requires_confirmation": False,
}


class ColmenaTool:
    def __init__(
        self,
        name: str,
        description: str,
        func,
        parameters: Dict[str, Any],
        category: str = "general",
        required_roles: List[str] = None,
        requires_confirmation: bool = False,
        examples: List[str] = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters
        self.category = category
        self.required_roles = required_roles or []
        self.requires_confirmation = requires_confirmation
        self.examples = examples or []

    async def execute(self, bridge: ApiBridge, **kwargs) -> Any:
        try:
            return await self.func(bridge, **kwargs)
        except ApiBridgeError as e:
            return e.to_dict()
        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {e}")
            return {"error": f"Error interno: {str(e)}"}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category,
            "required_roles": self.required_roles,
            "requires_confirmation": self.requires_confirmation,
            "examples": self.examples,
        }


class ToolRegistry:
    def __init__(self, token: str = None):
        self.tools: Dict[str, ColmenaTool] = {}
        self.bridge = ApiBridge(token) if token else None

    def set_token(self, token: str):
        self.bridge = ApiBridge(token)

    def register(self, tool: ColmenaTool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ColmenaTool]:
        return self.tools.get(name)

    def list_tools(self, role: str = None) -> List[Dict[str, Any]]:
        result = []
        for t in self.tools.values():
            if role and t.required_roles:
                if role != "superadmin" and role not in t.required_roles:
                    continue
            result.append(t.to_dict())
        return result


def _build_param(
    ptype: str,
    description: str,
    required: bool = False,
    default: Any = None,
    example: Any = None,
    enum: List[str] = None,
) -> dict:
    return {
        "type": ptype,
        "description": description,
        "required": required,
        "default": default,
        "example": example,
        "enum": enum,
    }


def _fmt_fields(params: dict) -> str:
    parts = []
    for name, p in params.items():
        label = "REQUERIDO" if p.get("required") else "opcional"
        enum_hint = f" ({', '.join(p['enum'])})" if p.get("enum") else ""
        parts.append(
            f"  - {name} ({p['type']}) [{label}]{enum_hint}: {p['description']}"
        )
    return "\n".join(parts)


def _build_fields_tools(registry: ToolRegistry):
    """Helper tools for exploring available fields and entities."""

    async def list_available_fields(bridge: ApiBridge, entity_type: str):
        """Muestra los campos disponibles (requeridos y opcionales) para crear una entidad."""
        fields_map = {
            "project": {
                "name": _build_param(
                    "string", "Nombre del proyecto", True, example="Curso de Python"
                ),
                "client_id": _build_param(
                    "string",
                    "ID o email del cliente",
                    True,
                    example="maria@ejemplo.com",
                ),
                "tipo_proyecto": _build_param(
                    "string",
                    "Tipo de proyecto",
                    True,
                    enum=[
                        "Curso",
                        "Diplomado",
                        "Taller",
                        "Manual",
                        "Multimedia",
                        "Otro",
                    ],
                ),
                "description": _build_param(
                    "string", "Descripcion del proyecto", False, default=""
                ),
                "idioma": _build_param(
                    "string", "Idioma principal", False, default="Espanol"
                ),
                "start_date": _build_param(
                    "string", "Fecha de inicio (YYYY-MM-DD)", True
                ),
                "end_date": _build_param("string", "Fecha de fin (YYYY-MM-DD)", False),
                "estado": _build_param(
                    "string",
                    "Estado del proyecto",
                    False,
                    default="Planificado",
                    enum=[
                        "Planificado",
                        "Activo",
                        "En pausa",
                        "Completado",
                        "Cancelado",
                    ],
                ),
            },
            "task": {
                "titulo": _build_param(
                    "string", "Titulo de la tarea", True, example="Crear modulo 1"
                ),
                "project_id": _build_param(
                    "integer", "ID del proyecto al que pertenece", True
                ),
                "descripcion": _build_param(
                    "string", "Descripcion detallada", False, default=""
                ),
                "asignado_a": _build_param("string", "User ID del responsable", False),
                "prioridad": _build_param(
                    "string",
                    "Prioridad",
                    False,
                    default="media",
                    enum=["baja", "media", "alta", "critica"],
                ),
                "estado": _build_param(
                    "string",
                    "Estado",
                    False,
                    default="pendiente",
                    enum=["pendiente", "en_progreso", "completada", "cancelada"],
                ),
                "fecha_entrega": _build_param(
                    "string", "Fecha de entrega (YYYY-MM-DD)", False
                ),
            },
            "client": {
                "email": _build_param(
                    "string",
                    "Correo electronico del cliente",
                    True,
                    example="cliente@ejemplo.com",
                ),
                "password": _build_param(
                    "string",
                    "Contrasena (se genera automaticamente si no se envia)",
                    False,
                ),
                "profile": _build_param(
                    "object",
                    "Objeto con datos del perfil: {pnombre, snombre, papellido, sapellido, telefono, direccion, ciudad, pais, tipo_entidad}",
                    True,
                ),
            },
            "user": {
                "email": _build_param("string", "Correo electronico", True),
                "nombre": _build_param("string", "Nombre completo", True),
                "password": _build_param("string", "Contrasena", False),
                "rol": _build_param(
                    "string", "Rol a asignar", False, default="registrado"
                ),
            },
            "resource": {
                "filename": _build_param("string", "Nombre del archivo", True),
                "file_type": _build_param(
                    "string",
                    "Tipo de archivo",
                    True,
                    enum=["pdf", "image", "video", "audio", "model"],
                ),
                "category": _build_param(
                    "string", "Categoria", True, example="imagenes-ia"
                ),
                "title": _build_param("string", "Titulo del recurso", True),
                "url": _build_param("string", "URL del archivo", True),
                "description": _build_param("string", "Descripcion", False),
            },
            "study_plan": {
                "name": _build_param("string", "Nombre del plan de estudio", True),
                "project_id": _build_param("integer", "ID del proyecto", True),
                "description": _build_param("string", "Descripcion", False),
            },
            "module": {
                "nombre_del_modulo": _build_param("string", "Nombre del modulo", True),
                "study_plan_id": _build_param(
                    "integer", "ID del plan de estudio", True
                ),
                "descripcion": _build_param("string", "Descripcion", False),
            },
        }
        info = fields_map.get(entity_type)
        if not info:
            return {
                "error": f"Entity type '{entity_type}' no soportado",
                "available": list(fields_map.keys()),
            }
        required = {k: v for k, v in info.items() if v["required"]}
        optional = {k: v for k, v in info.items() if not v["required"]}
        return {
            "entity_type": entity_type,
            "required_fields": required,
            "optional_fields": optional,
            "hint": f"Usa los campos REQUERIDOS primero. Si no tienes todos, pidele al usuario los que faltan uno por uno.",
        }

    registry.register(
        ColmenaTool(
            "list_available_fields",
            "Muestra los campos REQUERIDOS y OPCIONALES para crear una entidad. Usa esto ANTES de crear algo para saber que datos necesitas.",
            list_available_fields,
            {
                "entity_type": _build_param(
                    "string",
                    "Tipo de entidad: project, task, client, user, resource, study_plan, module",
                    True,
                    example="project",
                )
            },
            category="meta",
        )
    )


def _build_query_tools(registry: ToolRegistry):
    """Tools for querying data (GET endpoints)."""

    async def get_projects(bridge: ApiBridge, estado: str = None, limit: int = 50):
        """Lista proyectos. Opcionalmente filtra por estado."""
        return await bridge.get_projects(estado=estado, limit=limit)

    registry.register(
        ColmenaTool(
            "get_projects",
            "Obtiene la lista de proyectos. Opcional: filtra por estado (Planificado, Activo, En pausa, Completado, Cancelado).",
            get_projects,
            {
                "estado": _build_param(
                    "string",
                    "Filtrar por estado",
                    False,
                    enum=[
                        "Planificado",
                        "Activo",
                        "En pausa",
                        "Completado",
                        "Cancelado",
                    ],
                ),
                "limit": _build_param(
                    "integer", "Maximo de resultados", False, default=50
                ),
            },
            category="projects",
        )
    )

    async def get_project(bridge: ApiBridge, project_id: int):
        """Obtiene un proyecto por ID con todos sus detalles (tareas, cronograma)."""
        return await bridge.get_project(project_id)

    registry.register(
        ColmenaTool(
            "get_project",
            "Obtiene un proyecto especifico con todos sus detalles (incluye tareas y cronograma).",
            get_project,
            {"project_id": _build_param("integer", "ID del proyecto", True)},
            category="projects",
        )
    )

    async def search_projects(bridge: ApiBridge, query: str):
        """Busca proyectos por nombre o descripcion."""
        return await bridge.search(query)

    registry.register(
        ColmenaTool(
            "search_projects",
            "Busca proyectos por texto libre en nombre o descripcion.",
            search_projects,
            {"query": _build_param("string", "Texto a buscar", True)},
            category="projects",
        )
    )

    async def get_tasks(bridge: ApiBridge, project_id: int = None, limit: int = 50):
        """Lista tareas. Opcional: filtrar por proyecto."""
        return await bridge.get_tasks(project_id=project_id, limit=limit)

    registry.register(
        ColmenaTool(
            "get_tasks",
            "Obtiene lista de tareas. Opcionalmente filtra por project_id.",
            get_tasks,
            {
                "project_id": _build_param(
                    "integer", "ID del proyecto para filtrar", False
                ),
                "limit": _build_param(
                    "integer", "Maximo de resultados", False, default=50
                ),
            },
            category="tasks",
        )
    )

    async def get_task(bridge: ApiBridge, task_id: int):
        """Obtiene una tarea por ID."""
        return await bridge.get_task(task_id)

    registry.register(
        ColmenaTool(
            "get_task",
            "Obtiene una tarea especifica por ID.",
            get_task,
            {"task_id": _build_param("integer", "ID de la tarea", True)},
            category="tasks",
        )
    )

    async def get_users(bridge: ApiBridge, limit: int = 50):
        """Lista usuarios del sistema."""
        return await bridge.get_users(limit=limit)

    registry.register(
        ColmenaTool(
            "get_users",
            "Obtiene lista de usuarios del sistema.",
            get_users,
            {
                "limit": _build_param(
                    "integer", "Maximo de resultados", False, default=50
                )
            },
            category="users",
            required_roles=["superadmin", "admin", "coordinador", "abogado"],
        )
    )

    async def search_users(bridge: ApiBridge, query: str):
        """Busca usuarios por nombre o email."""
        return await bridge.search(query)

    registry.register(
        ColmenaTool(
            "search_users",
            "Busca usuarios por nombre o email.",
            search_users,
            {"query": _build_param("string", "Texto a buscar (nombre o email)", True)},
            category="users",
            required_roles=["superadmin", "admin", "coordinador", "abogado"],
        )
    )

    async def get_clients(bridge: ApiBridge, limit: int = 50):
        """Lista clientes del sistema."""
        return await bridge.get_clients(limit=limit)

    registry.register(
        ColmenaTool(
            "get_clients",
            "Obtiene lista de clientes.",
            get_clients,
            {
                "limit": _build_param(
                    "integer", "Maximo de resultados", False, default=50
                )
            },
            category="clients",
            required_roles=["superadmin", "admin", "coordinador", "abogado"],
        )
    )

    async def get_resources(bridge: ApiBridge, category: str = None, limit: int = 50):
        """Lista recursos/biblioteca. Opcional: filtrar por categoria."""
        return await bridge.get_resources(category=category, limit=limit)

    registry.register(
        ColmenaTool(
            "get_resources",
            "Obtiene lista de recursos de la biblioteca. Opcionalmente filtra por categoria.",
            get_resources,
            {
                "category": _build_param(
                    "string",
                    "Categoria (imagenes-ia, videos-ia, audios-ia, documentos, modelos-3d)",
                    False,
                ),
                "limit": _build_param(
                    "integer", "Maximo de resultados", False, default=50
                ),
            },
            category="resources",
        )
    )

    async def get_cronogramas(bridge: ApiBridge, project_id: int = None):
        """Lista cronogramas. Opcional: filtrar por proyecto."""
        return await bridge.get_cronogramas(project_id=project_id)

    registry.register(
        ColmenaTool(
            "get_cronogramas",
            "Obtiene cronogramas. Opcionalmente filtra por project_id.",
            get_cronogramas,
            {"project_id": _build_param("integer", "ID del proyecto", False)},
            category="cronogramas",
        )
    )

    async def get_fases(bridge: ApiBridge):
        """Lista todas las fases disponibles."""
        return await bridge.get_fases()

    registry.register(
        ColmenaTool(
            "get_fases",
            "Obtiene todas las fases del sistema.",
            get_fases,
            {},
            category="cronogramas",
        )
    )

    async def get_etapas(bridge: ApiBridge):
        """Lista todas las etapas disponibles."""
        return await bridge.get_etapas()

    registry.register(
        ColmenaTool(
            "get_etapas",
            "Obtiene todas las etapas del sistema.",
            get_etapas,
            {},
            category="cronogramas",
        )
    )

    async def get_study_plans(bridge: ApiBridge, project_id: int = None):
        """Lista planes de estudio. Opcional: filtrar por proyecto."""
        return await bridge.get_study_plans(project_id=project_id)

    registry.register(
        ColmenaTool(
            "get_study_plans",
            "Obtiene planes de estudio. Opcionalmente filtra por project_id.",
            get_study_plans,
            {"project_id": _build_param("integer", "ID del proyecto", False)},
            category="study_plans",
        )
    )

    async def get_participantes(bridge: ApiBridge, project_id: int):
        """Lista los participantes de un proyecto."""
        return await bridge.get_participantes(project_id)

    registry.register(
        ColmenaTool(
            "get_participantes",
            "Obtiene los participantes de un proyecto.",
            get_participantes,
            {"project_id": _build_param("integer", "ID del proyecto", True)},
            category="projects",
        )
    )

    async def get_health(bridge: ApiBridge):
        """Obtiene el diagnostico de salud del sistema (servicios, RAM, CPU, disco, SSL)."""
        return await bridge.get_health()

    registry.register(
        ColmenaTool(
            "get_health",
            "Obtiene el diagnostico completo del sistema: servicios, RAM, CPU, disco, SSL, Docker.",
            get_health,
            {},
            category="system",
            required_roles=["superadmin"],
        )
    )


def _build_mutation_tools(registry: ToolRegistry):
    """Tools for creating, updating, and deleting data (POST/PUT/PATCH/DELETE endpoints)."""

    async def create_project(bridge: ApiBridge, **kwargs):
        """Crea un NUEVO proyecto. REQUERIDO: name, client_id, tipo_proyecto.
        Paso a paso: si no tienes todos los datos, llama con los que tengas.
        La API te dira que campos faltan, entonces preguntale al usuario.
        Los IDs de clientes los puedes obtener con search_users o get_clients.
        """
        return await bridge.create_project(**kwargs)

    registry.register(
        ColmenaTool(
            "create_project",
            "Crea un nuevo proyecto. Requiere: name, client_id, tipo_proyecto. Opcional: description, idioma, start_date, end_date, estado, etapa.\n"
            "SI FALTAN CAMPOS: la API devolvera error de validacion con los campos REQUERIDOS. Pregunta al usuario uno por uno.",
            create_project,
            {
                "name": _build_param(
                    "string",
                    "Nombre del proyecto",
                    True,
                    example="Curso de Python Basico",
                ),
                "client_id": _build_param(
                    "string",
                    "ID (UUID) del cliente o su email para buscar",
                    True,
                    example="maria@ejemplo.com",
                ),
                "tipo_proyecto": _build_param(
                    "string",
                    "Tipo de proyecto",
                    True,
                    enum=[
                        "Curso",
                        "Diplomado",
                        "Taller",
                        "Manual",
                        "Multimedia",
                        "Otro",
                    ],
                ),
                "description": _build_param(
                    "string", "Descripcion del proyecto", False, default=""
                ),
                "idioma": _build_param(
                    "string", "Idioma principal", False, default="Espanol"
                ),
                "start_date": _build_param(
                    "string", "Fecha de inicio (YYYY-MM-DD)", False
                ),
                "end_date": _build_param("string", "Fecha de fin (YYYY-MM-DD)", False),
                "estado": _build_param(
                    "string", "Estado inicial", False, default="Planificado"
                ),
            },
            category="projects",
            requires_confirmation=True,
            required_roles=["superadmin", "admin", "coordinador", "abogado", "cliente"],
        )
    )

    async def update_project(bridge: ApiBridge, project_id: int, **kwargs):
        """Actualiza un proyecto existente. project_id es REQUERIDO. Solo envia los campos a modificar."""
        return await bridge.update_project(project_id, **kwargs)

    registry.register(
        ColmenaTool(
            "update_project",
            "Actualiza un proyecto existente. Solo necesitas project_id y los campos a modificar.",
            update_project,
            {
                "project_id": _build_param(
                    "integer", "ID del proyecto a actualizar", True
                ),
                "name": _build_param("string", "Nuevo nombre", False),
                "estado": _build_param(
                    "string",
                    "Nuevo estado",
                    False,
                    enum=[
                        "Planificado",
                        "Activo",
                        "En pausa",
                        "Completado",
                        "Cancelado",
                    ],
                ),
                "description": _build_param("string", "Nueva descripcion", False),
                "start_date": _build_param(
                    "string", "Nueva fecha inicio (YYYY-MM-DD)", False
                ),
                "end_date": _build_param(
                    "string", "Nueva fecha fin (YYYY-MM-DD)", False
                ),
            },
            category="projects",
            requires_confirmation=True,
            required_roles=["superadmin", "admin", "coordinador", "abogado"],
        )
    )

    async def delete_project(bridge: ApiBridge, project_id: int):
        """ELIMINA un proyecto permanentemente. REQUIERE CONFIRMACION."""
        return await bridge.delete_project(project_id)

    registry.register(
        ColmenaTool(
            "delete_project",
            "ELIMINA un proyecto permanentemente. Pide confirmacion al usuario antes de ejecutar.",
            delete_project,
            {"project_id": _build_param("integer", "ID del proyecto a eliminar", True)},
            category="projects",
            requires_confirmation=True,
            required_roles=["superadmin", "admin"],
        )
    )

    async def create_task(bridge: ApiBridge, **kwargs):
        """Crea una NUEVA tarea. REQUERIDO: titulo, project_id.
        Paso a paso: si faltan datos, la API te dira. Pregunta al usuario.
        """
        return await bridge.create_task(**kwargs)

    registry.register(
        ColmenaTool(
            "create_task",
            "Crea una nueva tarea. Requiere: titulo, project_id. Opcional: descripcion, asignado_a, prioridad, estado, fecha_entrega.\n"
            "Paso a paso: llama con lo que tengas. Si falta algo, la API te lo dira y le preguntas al usuario.",
            create_task,
            {
                "titulo": _build_param(
                    "string", "Titulo de la tarea", True, example="Disenar modulo 1"
                ),
                "project_id": _build_param("integer", "ID del proyecto", True),
                "descripcion": _build_param("string", "Descripcion detallada", False),
                "asignado_a": _build_param("string", "User ID del responsable", False),
                "prioridad": _build_param(
                    "string",
                    "Prioridad",
                    False,
                    default="media",
                    enum=["baja", "media", "alta", "critica"],
                ),
                "estado": _build_param("string", "Estado", False, default="pendiente"),
                "fecha_entrega": _build_param(
                    "string", "Fecha de entrega (YYYY-MM-DD)", False
                ),
            },
            category="tasks",
            requires_confirmation=True,
        )
    )

    async def update_task(bridge: ApiBridge, task_id: int, **kwargs):
        """Actualiza una tarea existente. Solo necesitas task_id y los campos a modificar."""
        return await bridge.update_task(task_id, **kwargs)

    registry.register(
        ColmenaTool(
            "update_task",
            "Actualiza una tarea existente. task_id es requerido. Solo enviar campos a modificar.",
            update_task,
            {
                "task_id": _build_param("integer", "ID de la tarea", True),
                "titulo": _build_param("string", "Nuevo titulo", False),
                "descripcion": _build_param("string", "Nueva descripcion", False),
                "prioridad": _build_param(
                    "string",
                    "Nueva prioridad",
                    False,
                    enum=["baja", "media", "alta", "critica"],
                ),
                "estado": _build_param(
                    "string",
                    "Nuevo estado",
                    False,
                    enum=["pendiente", "en_progreso", "completada", "cancelada"],
                ),
                "asignado_a": _build_param(
                    "string", "Nuevo responsable (user ID)", False
                ),
                "fecha_entrega": _build_param(
                    "string", "Nueva fecha entrega (YYYY-MM-DD)", False
                ),
            },
            category="tasks",
            requires_confirmation=True,
        )
    )

    async def delete_task(bridge: ApiBridge, task_id: int):
        """ELIMINA una tarea permanentemente. REQUIERE CONFIRMACION."""
        return await bridge.delete_task(task_id)

    registry.register(
        ColmenaTool(
            "delete_task",
            "ELIMINA una tarea. Pide confirmacion al usuario antes de ejecutar.",
            delete_task,
            {"task_id": _build_param("integer", "ID de la tarea a eliminar", True)},
            category="tasks",
            requires_confirmation=True,
            required_roles=["superadmin", "admin"],
        )
    )

    async def create_resource(bridge: ApiBridge, **kwargs):
        """Crea un nuevo recurso en la biblioteca. REQUERIDO: filename, file_type, category, title, url."""
        return await bridge.create_resource(**kwargs)

    registry.register(
        ColmenaTool(
            "create_resource",
            "Agrega un recurso a la biblioteca. Requiere: filename, file_type, category, title, url.",
            create_resource,
            {
                "filename": _build_param(
                    "string",
                    "Nombre del archivo con extension",
                    True,
                    example="imagen1.png",
                ),
                "file_type": _build_param(
                    "string",
                    "Tipo de archivo",
                    True,
                    enum=["pdf", "image", "video", "audio", "model"],
                ),
                "category": _build_param(
                    "string", "Categoria", True, example="imagenes-ia"
                ),
                "title": _build_param("string", "Titulo del recurso", True),
                "url": _build_param("string", "URL publica del archivo", True),
                "description": _build_param("string", "Descripcion", False),
                "thumbnail_url": _build_param("string", "URL del thumbnail", False),
            },
            category="resources",
            requires_confirmation=True,
        )
    )

    async def add_participante(bridge: ApiBridge, project_id: int, user_uid: str):
        """Agrega un participante a un proyecto."""
        return await bridge.add_participante(project_id, user_uid)

    registry.register(
        ColmenaTool(
            "add_participante",
            "Agrega un usuario como participante de un proyecto.",
            add_participante,
            {
                "project_id": _build_param("integer", "ID del proyecto", True),
                "user_uid": _build_param("string", "UUID del usuario a agregar", True),
            },
            category="projects",
            requires_confirmation=True,
            required_roles=["superadmin", "admin", "coordinador", "abogado"],
        )
    )

    async def remove_participante(bridge: ApiBridge, project_id: int, user_uid: str):
        """Elimina un participante de un proyecto."""
        return await bridge.remove_participante(project_id, user_uid)

    registry.register(
        ColmenaTool(
            "remove_participante",
            "Elimina un usuario como participante de un proyecto.",
            remove_participante,
            {
                "project_id": _build_param("integer", "ID del proyecto", True),
                "user_uid": _build_param("string", "UUID del usuario a eliminar", True),
            },
            category="projects",
            requires_confirmation=True,
            required_roles=["superadmin", "admin", "coordinador", "abogado"],
        )
    )

    async def create_study_plan(bridge: ApiBridge, **kwargs):
        """Crea un plan de estudio. REQUERIDO: name, project_id."""
        return await bridge.create_study_plan(**kwargs)

    registry.register(
        ColmenaTool(
            "create_study_plan",
            "Crea un nuevo plan de estudio. Requiere: name, project_id.",
            create_study_plan,
            {
                "name": _build_param("string", "Nombre del plan de estudio", True),
                "project_id": _build_param("integer", "ID del proyecto", True),
                "description": _build_param("string", "Descripcion", False),
            },
            category="study_plans",
            requires_confirmation=True,
            required_roles=["superadmin", "admin", "coordinador"],
        )
    )

    async def send_message(bridge: ApiBridge, **kwargs):
        """ENVIA un mensaje a otro usuario. REQUERIDO: receptor_uid, asunto, contenido."""
        return await bridge.send_message(**kwargs)

    registry.register(
        ColmenaTool(
            "send_message",
            "Envia un mensaje interno a otro usuario del sistema.",
            send_message,
            {
                "receptor_uid": _build_param(
                    "string", "UUID del usuario destinatario", True
                ),
                "asunto": _build_param("string", "Asunto del mensaje", True),
                "contenido": _build_param("string", "Contenido del mensaje", True),
            },
            category="messages",
            requires_confirmation=True,
        )
    )

    async def close_cronograma(bridge: ApiBridge, cronograma_id: int):
        """CIERRA un cronograma y activa el proyecto automaticamente."""
        return await bridge.close_cronograma(cronograma_id)

    registry.register(
        ColmenaTool(
            "close_cronograma",
            "Cierra un cronograma. Esto activa el proyecto automaticamente. REQUIERE CONFIRMACION.",
            close_cronograma,
            {
                "cronograma_id": _build_param(
                    "integer", "ID del cronograma a cerrar", True
                )
            },
            category="cronogramas",
            requires_confirmation=True,
            required_roles=["superadmin", "admin", "coordinador"],
        )
    )


def _build_system_tools(registry: ToolRegistry):
    """Tools for system operations - only for superadmin."""

    async def heal_service(bridge: ApiBridge, service_name: str):
        """Intenta revivir un servicio del sistema (virtualmind, mysql, apache2, mcp-gemini, etc.)."""
        return await bridge.heal_service(service_name)

    registry.register(
        ColmenaTool(
            "heal_service",
            "Intenta revivir un servicio caido del sistema. Solo para superadmin.",
            heal_service,
            {
                "service_name": _build_param(
                    "string",
                    "Nombre del servicio: virtualmind, mysql, apache2, mcp-gemini, mcp-ollama, ollama",
                    True,
                )
            },
            category="system",
            required_roles=["superadmin"],
            requires_confirmation=True,
        )
    )


def create_colmena_tools(token: str = None) -> ToolRegistry:
    registry = ToolRegistry(token=token)
    _build_fields_tools(registry)
    _build_query_tools(registry)
    _build_mutation_tools(registry)
    _build_system_tools(registry)
    return registry


colmena_tools_registry = create_colmena_tools()
