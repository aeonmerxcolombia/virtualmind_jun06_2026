import os
import secrets
from pathlib import Path

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)

from fastapi import FastAPI, Depends, HTTPException, status, Request
import ipaddress  # for IP validation
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.auth.auth_router import router as auth_router
from app.routes.tarea_router import router as tarea_router
from app.routes.permission_router import router as permission_router
from app.routes.role_router import router as role_router
from app.routes import chat
from app.routes import users
from app.routes.folder_router import router as folder_router
from app.routes.project_router import router as project_router
from app.routes.archivo_router import router as archivo_router
from app.routes import mensaje_router
from app.routes import config_routes
from app.routes import bulk_users
from app.routes import chat_cliente
from app.routes import generaraudios
from app.routes import log_router
from app.routes import module_router
from app.routes import study_plan_router
from app.routes.profile_router import router as profiles_router
from app.routes.client_router import router as client_router
from app.routes import podcast_router
from app.routes.competencia_router import router as competencia_router
from app.routes.solicitud_router import router as solicitud_router
from app.auth.password_recovery import router as password_recovery_router
from app.auth.reset_password_confirm import router as reset_password_confirm_router
from app.routes import unit_router
from app.routes.learning_activity_router import router as learning_activity_router
from app.routes import evaluacion_router
from app.routes import document_router
from app.routes.fase_router import router as fase_router
from app.routes.etapa_router import router as etapa_router
from app.routes.cronograma_router import router as cronograma_router
from app.routes import notification_router
from app.routes.author_content_form_router import router as author_content_form_router
from app.routes.instructional_design_form_router import router as instructional_design_form_router
from app.routes import resource_router
from app.routes import bitacora_router
from app.routes import contact_router
from app.routes import wanx_router
from app.routes import tripo_router
from app.routes import qwen_image_router
from app.routes import tts_router
from app.routes import lyria_router
from app.routes.ai_router import router as ai_router
from app.routes.ollama_router import router as ollama_router
from app.routes.ia_content_router import router as ia_content_router
from app.routes.tarea_ia_router import router as tarea_ia_router
from app.routes.audit_router import router as audit_router
from app.routes.documentos_router import router as documentos_router
from app.routes.documentos_office_router import router as documentos_office_router
from app.routes.face_router import router as face_router
from app.routes.presence_router import router as presence_router
from app.routes.audio_router import router as audio_router
from app.routes.laboratorio_vr_router import router
from app.routes.orquestador_router import router as orquestador_router
from app.routes.agente_rol_router import router as agente_rol_router
from app.routes.video_router import router as video_router
from app.routes.diagnostico_router import router as diagnostico_router

# === IMPORTACIÓN DEL MÓDULO ARTICULATE ===
from app.routes.articulate_router import router as articulate_router

# === BIBLIOTECA DE DOCUMENTOS ===
from app.routes.biblioteca_router import router as biblioteca_router

# === RRHH ===
from app.routes.rrhh_router import router as rrhh_router

# === NUEVO: ROUTER DE WHISPER ===
from app.routes.whisper_router import router as whisper_router

# === AUTENTICACIÓN POR VOZ Y HUELLA DACTILAR ===
from app.auth.voice_router import router as voice_router
from app.auth.webauthn_router import router as webauthn_router

# === NUEVO: ROUTER DE PARTICIPANTES DEL PROYECTO ===
from app.routes.proyecto_participantes_router import router as proyecto_participantes_router

# === NUEVO: VENCIMIENTOS Y AMPLIACIÓN DE TAREAS ===
from app.routes.vencimiento_router import router as vencimiento_router
from app.routes.ip_blacklist_router import router as ip_blacklist_router
from app.routes.clonar_voz_router import router as clonar_voz_router
from app.routes.videocast_router import router as videocast_router

# === GLOBAL SEARCH ===
from app.routes.search_router import router as search_router

# === AGENTIC OS - COLMENA ===
from app.colmena.router import router as colmena_router

# === AGENTIC OS - UNIFIED EXECUTOR ===
from app.routes.agentic_os_router import router as agentic_os_router


USER = "admin"
PASSWORD = "Babalon510.1.2.3.4.5.6.7.8_1"
security = HTTPBasic()

def auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, USER)
    correct_pass = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autorizado",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

import asyncio
from contextlib import asynccontextmanager
from app.colmena.evolution import SelfHealingAgent, ProfilerAgent, NightlySelfPlayArena, meta_factoria, finops
from app.colmena.orchestrator import event_bus

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.colmena.router import lymphocyte, scheduler, hibernator, rotator
    from app.services.hive_orchestrator import hive
    import logging
    logger = logging.getLogger("main.lifespan")

    hive.set_event_bus(event_bus)

    print("=" * 60)
    print("[COLMENA] Inicializando Agentic OS v5.0 - Enjambre de 31 Agentes")
    print("[COLMENA] ========================================")
    print("[COLMENA] 🟢 despachador_colmena   → Dispatcher (enrutador de comandos)")
    print("[COLMENA] 🟢 meta_factoria         → MetaFactoria (ciclo de vida de agentes)")
    print("[COLMENA] 🟢 self_play             → NightlySelfPlayArena (simulación 03:00 AM)")
    print("[COLMENA] 🟢 linfocito             → Lymphocyte (inmunología IP)")
    print("[COLMENA] 🟢 shadow_guardrail      → ShadowGuardrail (safety semántico)")
    print("[COLMENA] 🟢 insecto_planificador  → InsectoPlanificador (telemetría HW)")
    print("[COLMENA] 🟢 consolidacion_sinaptica → AgentSemanticGraph (memoria de éxitos)")
    print("[COLMENA] 🟢 adn_criptografico     → CryptoAdnGuard (firma de código)")
    print("[COLMENA] 🟢 hibernacion_sinaptica → HibernadorSinaptico (SQLite persistencia)")
    print("[COLMENA] 🟢 finops                → FinOpsAgent (tracking de costos API)")
    print("[COLMENA] 🟢 desarrollador_autosanador → SelfHealingAgent (auto-parchado)")
    print("[COLMENA] 🟢 perfilado_genetico    → ProfilerAgent (optimización NumPy)")
    print("[COLMENA] ========================================")
    print("[COLMENA] 🐝 HiveOrchestrator      → Cola de tareas entre agentes + polling sistema")
    print("[COLMENA] 🐝 EventBus persistente  → Eventos en SQLite para trazabilidad")

    async def hive_event_consumer(event):
        event_type = event.get("type", "")
        source = event.get("source", "unknown")
        target = event.get("target", "")
        task_id = event.get("task_id")
        outcome = event.get("outcome", "")

        # MetaFactoria: si una tarea de sistema falla, reintentar
        if event_type == "task_failed" and target and target.startswith("sistema_"):
            logger.info(f"[HIVE_CONSUMER] MetaFactoria detectó fallo en {target} tarea {task_id}")

        # Linfocito: auditar todas las tareas
        if event_type.startswith("task_"):
            logger.info(f"[HIVE_CONSUMER] [AUDIT] {source} -> {target}: {event_type} (task_id={task_id})")

        # Consolidacion sinaptica: guardar experiencias exitosas
        if event_type == "task_completed" and outcome == "completed":
            logger.info(f"[HIVE_CONSUMER] Experiencia exitosa registrada: {target} tarea {task_id}")

    event_bus.register_consumer(hive_event_consumer)

    print("[COLMENA] Lanzando loops background...")

    tasks = [
        asyncio.create_task(event_bus.start_consumer_loop(), name="eventbus"),
        asyncio.create_task(SelfHealingAgent.watch_loop(30), name="autosanador"),
        asyncio.create_task(ProfilerAgent.profile_loop(60), name="perfilador"),
        asyncio.create_task(NightlySelfPlayArena.scheduler_loop(), name="selfplay"),
        asyncio.create_task(finops.report_loop(finops, 300), name="finops"),
        asyncio.create_task(hive.poll_pending_system_tasks(interval=15), name="hive_poller"),
    ]
    print(f"[COLMENA] {len(tasks)} loops background activos. Enjambre interconectado funcional.")
    print("=" * 60)
    yield
    print("[COLMENA] Deteniendo agentes de sistema...")
    event_bus.stop()
    hive.stop()
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    print("[COLMENA] Enjambre detenido.")

app = FastAPI(
    title="Virtualmind API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

# === RUTAS PÚBLICAS - Permiten acceso sin token ===
PUBLIC_PATHS = {
    "/", "/docs", "/openapi.json",
    "/auth/login", "/auth/register", "/auth/google/callback", "/auth/facebook/callback",
    "/auth/request-password-reset", "/auth/verify-password-reset-code", "/auth/reset-password-confirm",
    "/auth/verify-2fa",
    "/auth/face/register", "/auth/face/login", "/auth/face/status",
    "/auth/voice/register", "/auth/voice/login", "/auth/voice/status",
    "/auth/webauthn/register/begin", "/auth/webauthn/register/complete",
    "/auth/webauthn/login/begin", "/auth/webauthn/login/complete",
    "/auth/webauthn/status",
    "/auth/activate-client",
    "/ai/health", "/ai/ollama/health", "/ollama/health",
    "/config/login-bg",
    "/static", "/static/",
    "/login.html", "/register", "/cambiarclave.html", "/accept-terms.html",
    "/onlyoffice-crear.html",
    "/documentos", "/documentos/", "/documentos/office/", "/documentos/office",
    "/video/", "/video",
    # Rutas OnlyOffice
    "/documentos-office/archivo", "/documentos-office/archivo/",
    "/documentos-office/callback", "/documentos-office/callback/",

    # Rutas comunes frontend
    "/assets/", "/js/", "/css/", "/images/", "/fonts/",
    "/users/", "/users",
    "/profiles/", "/profiles",
    "/roles/", "/roles",
    "/permissions/", "/permissions",
    "/notifications/", "/notifications",
    "/modules/", "/modules",
    "/tareas/", "/tareas",
    "/tripo3d/model", "/tripo3d/model/",
    "/ws/agent", "/ws/agent/",
    "/colmena/health", "/colmena/permissions", "/colmena/",
    "/chat/", "/chat",
    "/fases/", "/fases",
    "/etapas/", "/etapas",
    "/unidades/", "/unidades",
    "/projects/", "/projects",
    "/folders/", "/folders",
    "/archivos/", "/archivos",
    "/competencias/", "/competencias",
    "/study-plans/", "/study-plans",
    "/learning-activities/", "/learning-activities",
    "/evaluaciones/", "/evaluaciones",
    "/bitacora/", "/bitacora",
    "/config/", "/config",
    "/clients/", "/clients",
    "/solicitudes/", "/solicitudes",
    "/audits/", "/audits",
    "/courses/", "/courses",
    "/units/", "/units",
    "/crm/", "/crm",
    "/generaraudios/", "/generaraudios",
    "/podcast/", "/podcast",
    "/tareas-ia/", "/tareas-ia",
    "/orquestador-ia/disparar", "/orquestador-ia/",
    "/agentes-rol/", "/agentes-rol",
    "/agentic-os/", "/agentic-os",
    "/logs/", "/logs",
    "/recursos/", "/recursos",
    "/contacto/", "/contacto",

    # === RUTAS ARTICULATE (Sin validación de token) ===
    "/articulate/", "/articulate",

    # Biblioteca de documentos
    "/biblioteca/", "/biblioteca",

    # === NUEVO: RUTAS DE WHISPER PÚBLICAS ===
    "/whisper/", "/whisper",

    # === NUEVO: RUTAS DE PARTICIPANTES PÚBLICAS FRONTEXT COMPATIBLE ===
    "/participantes", "/participantes/",

    # Vencimientos (público para cron)
    "/vencimientos/", "/vencimientos",

    # RRHH
    "/rrhh", "/rrhh/",
}

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Dejar pasar el preflight de CORS sin pedir token
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path

    if path.startswith("/static"):
        return await call_next(request)

    for p in PUBLIC_PATHS:
        if p != "/static" and (path == p or path.startswith(p.rstrip("/") + "/")):
            return await call_next(request)

    # Aceptar token por header Authorization O por query param ?token=
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "") if auth_header else None

    # Si no hay token en header, intentar con query param
    if not token:
        token = request.query_params.get("token")

    # Agregar token de query params siempre para compatibilidad con frontend
    query_token = request.query_params.get("token")
    if query_token and not token:
        token = query_token

    if not token:
        print(f"[AUTH] No token provided for path: {path}")
        return JSONResponse(
            status_code=401,
            content={"detail": "Token de autenticación requerido"}
        )

    from app.auth.jwt_handler import decodeJWT
    payload = decodeJWT(token)
    if not payload:
        print(f"[AUTH] Invalid/expired token for path: {path}, token: {token[:50]}...")
        return JSONResponse(
            status_code=401,
            content={"detail": "Token inválido o expirado"}
        )

    print(f"[AUTH] Token valid for path: {path}, user: {payload.get('sub')}, payload: {payload}")
    request.state.user = payload
    return await call_next(request)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def ip_blacklist_middleware(request: Request, call_next):
    from app.ip_blacklist import is_ip_blocked
    client_ip = request.client.host if request.client else None
    if client_ip and is_ip_blocked(client_ip):
        return JSONResponse(status_code=403, content={"detail": "Acceso denegado: IP bloqueada"})
    response = await call_next(request)
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Content-Security-Policy'] = "frame-ancestors *"
    return response

BASE_DIR = os.getcwd()
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/audios", StaticFiles(directory="/home/ubuntu/audios"), name="audios")

routers = [
    auth_router, users.router, chat.router,
    permission_router, role_router,
    folder_router, archivo_router, mensaje_router.router,
    config_routes.router, bulk_users.router, chat_cliente.router,
    generaraudios.router, log_router.router, profiles_router,
    client_router,
    podcast_router.router, competencia_router,
    solicitud_router, password_recovery_router,
    reset_password_confirm_router, project_router,
    study_plan_router.router, module_router.router,
    unit_router.router, learning_activity_router,
    tarea_router, evaluacion_router.router,
    document_router.router,
    fase_router, etapa_router, cronograma_router,
    notification_router.router,
    author_content_form_router,
    instructional_design_form_router,
    video_router,

    # === REGISTRO DEL ROUTER ARTICULATE ===
    articulate_router,

    # === REGISTRO DEL NUEVO ROUTER DE WHISPER ===
    whisper_router,

    # === REGISTRO DEL NUEVO ROUTER DE PARTICIPANTES ===
    proyecto_participantes_router,

    # === AUTENTICACIÓN POR VOZ Y HUELLA ===
    voice_router,
    webauthn_router,
]

app.include_router(resource_router.router)
app.include_router(bitacora_router.router)

for r in routers:
    app.include_router(r)

app.include_router(contact_router.router)
app.include_router(wanx_router.router)
app.include_router(tripo_router.router)
app.include_router(qwen_image_router.router)
app.include_router(tts_router.router)
app.include_router(lyria_router.router)
app.include_router(ai_router)
app.include_router(ollama_router)
app.include_router(ia_content_router)
app.include_router(tarea_ia_router)
app.include_router(audit_router)
app.include_router(documentos_router)
app.include_router(documentos_office_router)
app.include_router(face_router)
app.include_router(presence_router)
app.include_router(audio_router)
app.include_router(router)
app.include_router(orquestador_router)
app.include_router(agente_rol_router)
app.include_router(colmena_router)
app.include_router(agentic_os_router)
app.include_router(diagnostico_router)
app.include_router(biblioteca_router)
app.include_router(rrhh_router)
app.include_router(vencimiento_router)
app.include_router(ip_blacklist_router)
app.include_router(clonar_voz_router)
app.include_router(videocast_router)
app.include_router(search_router)

@app.get("/")
def read_root():
    return {"message": "API de Virtualmind funcionando"}

@app.get("/docs", response_class=HTMLResponse)
def swagger_docs():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Swagger UI")

@app.get("/openapi.json")
def openapi_json():
    return app.openapi()
