"""
ApiBridge — Cliente HTTP que llama los endpoints reales de FastAPI con JWT.
Reemplaza el acceso directo a DB, asegurando auth, RBAC y lógica de negocio.
"""
import json
import httpx
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

BASE_URL = "https://localhost:8000"
TIMEOUT = 30


class ApiBridgeError(Exception):
    def __init__(self, message: str, status_code: int = 400, details: Any = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


class ApiBridge:
    def __init__(self, token: str, base_url: str = BASE_URL):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=False, timeout=TIMEOUT, base_url=self.base_url
            )
        return self._client

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> Any:
        client = await self._get_client()
        url = path.lstrip("/")
        try:
            resp = await client.request(
                method, url, headers=self._headers(), **kwargs
            )
        except httpx.ConnectError:
            raise ApiBridgeError(
                f"No se pudo conectar al backend en {self.base_url}",
                status_code=503,
            )
        except httpx.TimeoutException:
            raise ApiBridgeError(
                f"Timeout al conectar con {self.base_url}/{url}", status_code=504
            )

        if resp.status_code == 401:
            raise ApiBridgeError(
                "No autorizado. Tu token no tiene acceso a este recurso.",
                status_code=401,
            )
        if resp.status_code == 403:
            raise ApiBridgeError(
                "Acceso denegado. Tu rol no tiene permiso para esta accion.",
                status_code=403,
            )
        if resp.status_code == 422:
            errors = resp.json().get("detail", [])
            msgs = []
            for e in errors:
                loc = " -> ".join(str(x) for x in e.get("loc", []))
                msg = e.get("msg", "")
                msgs.append(f"{loc}: {msg}" if loc else msg)
            raise ApiBridgeError(
                "Error de validacion. Campos requeridos faltantes o invalidos.",
                status_code=422,
                details={"validation_errors": errors, "messages": msgs},
            )
        if resp.status_code == 404:
            raise ApiBridgeError("Recurso no encontrado", status_code=404)
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise ApiBridgeError(
                f"Error del servidor: {resp.status_code}",
                status_code=resp.status_code,
                details=detail,
            )

        if resp.status_code == 204:
            return {"success": True, "message": "Operacion completada"}

        try:
            return resp.json()
        except Exception:
            return {"success": True, "status_code": resp.status_code}

    # ===================== PROJECTS =====================
    async def get_projects(self, estado: str = None, limit: int = 50) -> list:
        params = {"limit": limit}
        if estado:
            params["estado"] = estado
        return await self._request("GET", "/projects/", params=params)

    async def get_project(self, project_id: int) -> dict:
        return await self._request("GET", f"/projects/{project_id}")

    async def create_project(self, **data) -> dict:
        return await self._request("POST", "/projects/", json=data)

    async def update_project(self, project_id: int, **data) -> dict:
        return await self._request("PUT", f"/projects/{project_id}", json=data)

    async def delete_project(self, project_id: int) -> dict:
        return await self._request("DELETE", f"/projects/{project_id}")

    # ===================== TASKS =====================
    async def get_tasks(self, project_id: int = None, limit: int = 50) -> list:
        params = {"limit": limit}
        if project_id:
            params["project_id"] = project_id
        return await self._request("GET", "/tareas/", params=params)

    async def get_task(self, task_id: int) -> dict:
        return await self._request("GET", f"/tareas/{task_id}")

    async def create_task(self, **data) -> dict:
        return await self._request("POST", "/tareas/", json=data)

    async def update_task(self, task_id: int, **data) -> dict:
        return await self._request("PUT", f"/tareas/{task_id}", json=data)

    async def delete_task(self, task_id: int) -> dict:
        return await self._request("DELETE", f"/tareas/{task_id}")

    # ===================== USERS =====================
    async def get_users(self, limit: int = 50) -> list:
        return await self._request("GET", "/users/", params={"limit": limit})

    async def get_user(self, user_id: str) -> dict:
        return await self._request("GET", f"/users/{user_id}")

    async def create_user(self, **data) -> dict:
        return await self._request("POST", "/auth/register", json=data)

    async def update_user(self, user_id: str, **data) -> dict:
        return await self._request("PUT", f"/users/{user_id}", json=data)

    async def delete_user(self, user_id: str) -> dict:
        return await self._request("DELETE", f"/users/{user_id}")

    # ===================== CLIENTS =====================
    async def get_clients(self, limit: int = 50) -> list:
        return await self._request("GET", "/clients/", params={"limit": limit})

    async def get_client(self, user_id: str) -> dict:
        return await self._request("GET", f"/clients/{user_id}")

    async def create_client(self, **data) -> dict:
        return await self._request("POST", "/clients/", json=data)

    async def update_client(self, user_id: str, **data) -> dict:
        return await self._request("PATCH", f"/clients/{user_id}", json=data)

    # ===================== RESOURCES =====================
    async def get_resources(self, category: str = None, limit: int = 50) -> list:
        params = {"limit": limit}
        if category:
            params["category"] = category
        return await self._request("GET", "/resources/", params=params)

    async def create_resource(self, **data) -> dict:
        return await self._request("POST", "/resources/", json=data)

    async def create_resource_from_url(self, **data) -> dict:
        return await self._request("POST", "/resources/from-url", json=data)

    # ===================== CRONOGRAMAS =====================
    async def get_cronogramas(self, project_id: int = None) -> list:
        if project_id:
            return await self._request("GET", f"/cronogramas/project/{project_id}")
        return await self._request("GET", "/cronogramas/")

    async def get_cronograma(self, cronograma_id: int) -> dict:
        return await self._request("GET", f"/cronogramas/{cronograma_id}")

    async def create_cronograma(self, **data) -> dict:
        return await self._request("POST", "/cronogramas/", json=data)

    async def update_cronograma(self, cronograma_id: int, **data) -> dict:
        return await self._request("PUT", f"/cronogramas/{cronograma_id}", json=data)

    async def close_cronograma(self, cronograma_id: int) -> dict:
        return await self._request("PATCH", f"/cronogramas/{cronograma_id}/cerrar")

    # ===================== STUDY PLANS =====================
    async def get_study_plans(self, project_id: int = None) -> list:
        params = {}
        if project_id:
            params["project_id"] = project_id
        return await self._request("GET", "/study-plans/", params=params)

    async def create_study_plan(self, **data) -> dict:
        return await self._request("POST", "/study-plans/", json=data)

    # ===================== MODULES =====================
    async def get_modules(self, study_plan_id: int = None) -> list:
        params = {}
        if study_plan_id:
            params["study_plan_id"] = study_plan_id
        return await self._request("GET", "/modules/", params=params)

    async def create_module(self, **data) -> dict:
        return await self._request("POST", "/modules/", json=data)

    # ===================== SEARCH =====================
    async def search(self, query: str, limit: int = 10) -> list:
        return await self._request(
            "GET", "/search/", params={"q": query, "limit": limit}
        )

    # ===================== FASES / ETAPAS =====================
    async def get_fases(self) -> list:
        return await self._request("GET", "/fases/")

    async def get_etapas(self) -> list:
        return await self._request("GET", "/etapas/")

    # ===================== PROYECTO PARTICIPANTES =====================
    async def get_participantes(self, project_id: int) -> list:
        return await self._request(
            "GET", f"/proyecto-participantes/{project_id}"
        )

    async def add_participante(self, project_id: int, user_uid: str) -> dict:
        return await self._request(
            "POST",
            "/proyecto-participantes/",
            json={"project_id": project_id, "user_uid": user_uid},
        )

    async def remove_participante(self, project_id: int, user_uid: str) -> dict:
        return await self._request(
            "DELETE", f"/proyecto-participantes/{project_id}/{user_uid}"
        )

    # ===================== DIAGNOSTICO =====================
    async def get_health(self) -> dict:
        return await self._request("GET", "/diagnostico/")

    async def heal_service(self, service_name: str) -> dict:
        return await self._request(
            "POST", "/diagnostico/heal", params={"service": service_name}
        )

    # ===================== BIBLIOTECA =====================
    async def get_biblioteca(self, limit: int = 50) -> list:
        return await self._request("GET", "/biblioteca/", params={"limit": limit})

    async def get_biblioteca_doc(self, doc_id: int) -> dict:
        return await self._request("GET", f"/biblioteca/{doc_id}")

    async def get_biblioteca_permisos(self, doc_id: int) -> list:
        return await self._request("GET", f"/biblioteca/{doc_id}/permisos")

    # ===================== MENSAJES =====================
    async def get_inbox(self, limit: int = 20) -> list:
        return await self._request("GET", "/mensajes/inbox", params={"limit": limit})

    async def send_message(self, **data) -> dict:
        return await self._request("POST", "/mensajes/", json=data)

    # ===================== RRHH =====================
    async def get_rrhh(self) -> list:
        return await self._request("GET", "/rrhh/hoja-vida/")

    async def get_rrhh_by_project(self, project_id: int) -> list:
        return await self._request(
            "GET", f"/rrhh/hoja-vida/proyecto/{project_id}"
        )
