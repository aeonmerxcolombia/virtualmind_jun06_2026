import json
import traceback
import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from app.colmena.config import settings
from app.colmena.security import (
    ShadowGuardrail, CryptoAdnGuard, WebSocketSymmetricRotator,
    LymphocyteBehavioralMonitor, AgentContext, get_ws_agent_context, check_ws_permission, get_token_from_header
)
from app.colmena.orchestrator import event_bus, InsectoPlanificador, HibernadorSinaptico
from app.colmena.dispatcher import dispatcher, connection_manager
from app.colmena.database import AsyncSessionLocal
from app.colmena.tools import create_colmena_tools
from sqlalchemy import text

router = APIRouter(tags=["colmena"])

scheduler = InsectoPlanificador()
hibernator = HibernadorSinaptico()
lymphocyte = LymphocyteBehavioralMonitor()
rotator = WebSocketSymmetricRotator(settings.CODE_SIGN_KEY)

active_ram_contexts: Dict[str, Any] = {}

async def audit_honeypot_triggered(client_ip: str):
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT triggered_at FROM sys_security_honeypot WHERE id = 1;"))
            row = result.fetchone()
            if row and row[0] is not None:
                print(f"[AUDITORÍA] HONEYPOT DETONADO! Baneo IP: {client_ip}")
                lymphocyte.banned_ips.add(client_ip)
    except Exception:
        pass

@router.websocket("/ws/agent/{role}")
async def websocket_agent_endpoint(websocket: WebSocket, role: str):
    client_ip = websocket.client.host

    await audit_honeypot_triggered(client_ip)
    if lymphocyte.is_banned(client_ip):
        await websocket.close(code=4001)
        return

    if role not in settings.ROLES_INTERFAZ and role not in settings.ROLES_SISTEMA:
        await websocket.close(code=4003)
        return

    agent_ctx = await get_ws_agent_context(websocket)
    if not agent_ctx:
        await websocket.close(code=4001, reason="Token JWT requerido como query param")
        return

    if role in settings.ROLES_INTERFAZ and role not in agent_ctx.roles:
        is_superadmin = "superadmin" in agent_ctx.roles
        print(f"[DEBUG] User {agent_ctx.email} roles: {agent_ctx.roles} | Requested role: {role} | Superadmin: {is_superadmin}")
        if not is_superadmin:
            await websocket.close(code=4003, reason="Rol no autorizado para este usuario")
            return

    await websocket.accept()
    print(f"[COLMENA] Canal seguro establecido para Rol: {role} Usuario: {agent_ctx.email} IP: {client_ip}")

    connection_manager.add(role, websocket)

    try:
        while True:
            raw_data = await websocket.receive_text()
            lymphocyte.audit_traffic(client_ip)

            try:
                decrypted_data = rotator.decrypt(raw_data)
                message_packet = json.loads(decrypted_data)
            except Exception:
                await websocket.send_text(rotator.encrypt(json.dumps({"type": "error", "message": "Formato de mensaje inválido"})))
                continue

            action = message_packet.get("action")
            command = message_packet.get("command", "")
            text_input = message_packet.get("text", "")

            if action == "page_blur":
                if role in active_ram_contexts:
                    hibernator.hibernate_agent(role, active_ram_contexts[role])
                    del active_ram_contexts[role]
                response = {"status": "sinapsis_hibernada", "role": role}
                await websocket.send_text(rotator.encrypt(json.dumps(response)))
                continue

            elif action == "page_focus":
                recovered_state = hibernator.restore_agent(role)
                if recovered_state:
                    active_ram_contexts[role] = recovered_state
                response = {"status": "sinapsis_activa", "role": role}
                await websocket.send_text(rotator.encrypt(json.dumps(response)))
                continue

            elif action == "get_hardware_telemetry":
                if not check_ws_permission(agent_ctx, "colmena:view_telemetry"):
                    response = {"type": "error", "message": "Permiso 'colmena:view_telemetry' requerido"}
                    await websocket.send_text(rotator.encrypt(json.dumps(response)))
                    continue
                telemetry = await scheduler.get_hardware_telemetry()
                await websocket.send_text(rotator.encrypt(json.dumps({"type": "telemetry", "data": telemetry})))
                continue

            input_text = command or text_input
            if not input_text:
                await websocket.send_text(rotator.encrypt(json.dumps({"type": "error", "message": "Envia un comando o texto"})))
                continue

            if len(input_text) > 4096:
                await websocket.send_text(rotator.encrypt(json.dumps({"type": "error", "message": "Texto demasiado largo (máx 4096 caracteres)"})))
                continue

            is_safe = await ShadowGuardrail.validate_semantic_safety(input_text, role)
            if not is_safe:
                response = {"type": "security_alert", "message": "Invasión Semántica Interceptada"}
                await websocket.send_text(rotator.encrypt(json.dumps(response)))
                continue

            telemetry = await scheduler.get_hardware_telemetry()
            if telemetry["system_stress_critical"]:
                response = {"type": "system_action", "action": "degrade_ui", "reason": "RAM/CPU en niveles límite"}
                await websocket.send_text(rotator.encrypt(json.dumps(response)))
                continue

            result = await dispatcher.dispatch(input_text, role, agent_ctx, websocket)
            await websocket.send_text(rotator.encrypt(json.dumps(result)))

    except WebSocketDisconnect:
        print(f"[COLMENA] WebSocket cerrado para rol {role}")
        connection_manager.remove(role, websocket)


class NLURequest(BaseModel):
    text: str
    role: str
    context_id: Optional[str] = None

class NLUResponse(BaseModel):
    corrected_text: str
    intent: str
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = {}
    confidence: float = 0.0
    explanation: str = ""
    response: str = ""
    role: str = ""

_nlu_contexts: Dict[str, list] = {}

async def _get_tools_for_role(role: str, token: str) -> list:
    registry = create_colmena_tools(token=token)
    return registry.list_tools(role=role)

@router.post("/colmena/nlu", response_model=NLUResponse)
async def colmena_nlu(req: NLURequest, token: str = Depends(get_token_from_header)):
    from app.services.ai.mcp_service import mcp_service

    role = req.role
    text = req.text
    ctx_id = req.context_id or f"{token[:16]}_{role}"

    if ctx_id not in _nlu_contexts:
        _nlu_contexts[ctx_id] = []

    tools_list = await _get_tools_for_role(role, token)
    tools_json = json.dumps([{
        "name": t["name"],
        "description": t["description"],
        "parameters": t.get("parameters", {}),
        "category": t.get("category", "general")
    } for t in tools_list], indent=2, ensure_ascii=False)

    context_history = _nlu_contexts[ctx_id][-5:]
    history_str = "\n".join(context_history) if context_history else "Sin historial."

    nlu_prompt = (
        f"Eres un asistente NLU experto en la plataforma VirtualMind LMS. "
        f"El usuario con rol '{role}' ha escrito un comando en lenguaje natural. "
        f"Tu trabajo es:\n"
        f"1. CORREGIR errores ortográficos y tipográficos\n"
        f"2. ENTENDER la intención del usuario\n"
        f"3. ELEGIR la herramienta correcta de las disponibles\n"
        f"4. EXTRAER los parámetros de la herramienta\n\n"
        f"HISTORIAL DE LA CONVERSACIÓN:\n{history_str}\n\n"
        f"HERRAMIENTAS DISPONIBLES PARA ROL '{role}':\n{tools_json}\n\n"
        f"COMANDO DEL USUARIO: \"{text}\"\n\n"
        f"Responde EXACTAMENTE con este JSON (sin markdown):\n"
        f"{{\n"
        f'  "corrected_text": "comando corregido con ortografía correcta",\n'
        f'  "intent": "query|create|update|delete|list|analyze|generate|background|unknown",\n'
        f'  "tool_name": "nombre_exacto_de_la_herramienta_o_vacío_si_no_hay_match",\n'
        f'  "parameters": {{"param1": "valor1"}},\n'
        f'  "confidence": 0.95,\n'
        f'  "explanation": "breve explicación de lo que entendiste",\n'
        f'  "response": "respuesta amigable al usuario en español"'
        f"\n}}"
    )

    try:
        result = mcp_service.generate_json(
            prompt=nlu_prompt,
            system_instruction=(
                "Eres un clasificador NLU de VirtualMind. "
                "Corrige errores tipográficos, extrae intenciones y mapea a herramientas. "
                "Responde SOLO con JSON válido. "
                "Si no hay match de herramienta, devuelve tool_name vacío e intent 'unknown'."
            ),
            temperature=0.1,
            max_tokens=1024,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en NLU: {str(e)}")

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    corrected = result.get("corrected_text", text)
    intent = result.get("intent", "unknown")
    tool_name = result.get("tool_name", "")
    params = result.get("parameters", {})
    confidence = result.get("confidence", 0.0)
    explanation = result.get("explanation", "")
    response_text = result.get("response", "")

    _nlu_contexts[ctx_id].append(f"User: {text} -> NLU: {corrected} (tool: {tool_name}, intent: {intent})")

    return NLUResponse(
        corrected_text=corrected,
        intent=intent,
        tool_name=tool_name,
        parameters=params,
        confidence=confidence,
        explanation=explanation,
        response=response_text,
        role=role,
    )


@router.get("/colmena/permissions")
async def get_required_permissions():
    return {
        "colmena:view_telemetry": "Ver telemetría del hardware",
        "colmena:background_task": "Ejecutar tareas pesadas en segundo plano",
        "colmena:admin": "Operaciones de administración de la colmena"
    }

@router.get("/colmena/health")
async def colmena_health():
    telemetry = await scheduler.get_hardware_telemetry()
    return {
        "status": "active",
        "version": "5.0",
        "hibernated_agents": hibernator.db_path,
        "banned_ips": list(lymphocyte.banned_ips),
        "active_ram_contexts": list(active_ram_contexts.keys()),
        "telemetry": telemetry
    }
