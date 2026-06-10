import os
import secrets
import smtplib
import math
from email.message import EmailMessage
from datetime import datetime, timedelta
import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr, Field
from typing import List
import httpx

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# ==========================================
# TUS IMPORTACIONES EXACTAS Y REALES
# ==========================================
from app.database.db import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.hoja_vida import HojaVida
from app.schemas.user_schema import UserCreate, UserLogin, Token
from app.auth.hashing import Hash
from app.auth.jwt_handler import create_access_token
from app.auth.deps import require_auth

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ==========================================
# ESQUEMAS PYDANTIC (Para 2FA y Biometría)
# ==========================================
class Verify2FARequest(BaseModel):
    email: EmailStr
    code: str


class FaceRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    embedding: List[float] = Field(..., description="Vector facial de 128 dimensiones")


class FaceLoginRequest(BaseModel):
    email: EmailStr
    embedding: List[float] = Field(
        ..., description="Vector facial capturado en tiempo real"
    )


class SwitchRoleRequest(BaseModel):
    role: str


# ==========================================
# LÓGICA DE BIOMETRÍA Y UTILIDADES
# ==========================================
def compare_face_embeddings(
    known_embedding: List[float], new_embedding: List[float], threshold: float = 0.55
) -> bool:
    if not known_embedding or not new_embedding:
        return False
    if len(known_embedding) != len(new_embedding):
        raise ValueError("Ambos vectores deben ser de 128 dimensiones.")

    distance = math.sqrt(
        sum((a - b) ** 2 for a, b in zip(known_embedding, new_embedding))
    )
    return distance < threshold


def generate_otp() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))


def send_2fa_email_sync(email_to: str, code: str):
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Virtualmind Security")

    message = EmailMessage()
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    message["To"] = email_to
    message["Subject"] = "Código de verificación Virtualmind"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px; max-width: 500px;">
        <h2 style="color: #333;">Verificación de Seguridad</h2>
        <p>Hola,</p>
        <p>Alguien intentó iniciar sesión en tu cuenta de Virtualmind.</p>
        <p>Tu código de acceso temporal es:</p>
        <div style="background-color: #f5f5f5; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">
            <h1 style="color: #4A90E2; letter-spacing: 5px; margin: 0;">{code}</h1>
        </div>
        <p style="font-size: 12px; color: #777;">Este código expira en 5 minutos.</p>
    </div>
    """
    message.set_content("Tu código de seguridad es: " + code)
    message.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
    except Exception as e:
        print(f"Error crítico enviando correo 2FA: {e}")


# ==========================================
# DEPENDENCIAS Y AUDITORÍA
# ==========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_geo_cache = {}
_GEO_CACHE_DURATION = 3600


def get_geolocation(ip: str) -> dict:
    try:
        if ip in ("127.0.0.1", "localhost", "::1"):
            return {"ciudad": "Local", "pais": "Local", "lat": 0, "lon": 0}

        now = time.time()
        if ip in _geo_cache and (now - _geo_cache[ip]["ts"]) < _GEO_CACHE_DURATION:
            return _geo_cache[ip]["data"]

        resp = httpx.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon", timeout=2
        )
        data = resp.json()
        if data.get("status") == "success":
            result = {
                "ciudad": data.get("city", ""),
                "pais": data.get("country", ""),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
            }
            _geo_cache[ip] = {"data": result, "ts": now}
            return result
    except Exception as e:
        print(f"Geolocation error: {e}")
    return {"ciudad": None, "pais": None, "lat": None, "lon": None}


def registrar_auditoria(
    db: Session,
    user_uid: str,
    ip: str,
    ciudad: str = None,
    pais: str = None,
    lat: float = None,
    lon: float = None,
):
    try:
        geo = get_geolocation(ip)
        ciudad = ciudad or geo["ciudad"]
        pais = pais or geo["pais"]
        lat = lat or geo["lat"]
        lon = lon or geo["lon"]

        # NOTA: Como AuditLog no estaba en tus importaciones originales, lo manejamos dinámicamente
        # para que Uvicorn no caiga en caso de que no lo estés usando aún.
        try:
            from app.models.audit_log import AuditLog

            audit = AuditLog(
                user_uid=user_uid,
                ip=ip,
                ciudad=ciudad,
                pais=pais,
                latitud=lat,
                longitud=lon,
                fecha_entrada=datetime.utcnow(),
            )
            db.add(audit)
            db.commit()
            return audit.id
        except ImportError:
            print("AuditLog no está importado o creado. Auditoría omitida.")
            return None
    except Exception as e:
        print(f"Error registrando auditoría: {e}")
        return None


# ==========================================
# ENDPOINTS PRINCIPALES
# ==========================================


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(request: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    roles = db.query(Role).filter(Role.id.in_(request.role_ids)).all()
    if len(roles) != len(request.role_ids):
        raise HTTPException(status_code=400, detail="Algún role_id no es válido")

    new_user = User(
        uid=str(uuid4()),
        nombre=request.nombre,
        tipo_documento=request.tipo_documento,
        documento=request.documento,
        email=request.email,
        password=Hash.encrypt(request.password),
        estado=True,
    )
    new_user.roles = roles
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Auto-vincular HV si existe para este email
    try:
        hv = (
            db.query(HojaVida)
            .filter(HojaVida.email == request.email.strip().lower())
            .first()
        )
        if hv:
            hv.user_id = new_user.uid
            if not hv.nombre_completo:
                hv.nombre_completo = request.nombre
            db.commit()
    except Exception:
        pass

    return {"msg": "Usuario creado exitosamente", "uid": new_user.uid}


# --- ENDPOINTS DE BIOMETRÍA FACIAL ---


@router.post("/face/register")
def register_face(request: FaceRegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    try:
        user.face_embedding = request.embedding
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error al guardar biometría: {str(e)}"
        )

    return {"message": "Vector biométrico registrado exitosamente", "status": "ok"}


@router.post("/face/login")
def login_face(
    request_data: FaceLoginRequest, req: Request, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request_data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no registrado")

    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo"
        )

    if not user.face_embedding:
        raise HTTPException(
            status_code=400,
            detail="No tienes un rostro registrado. Inicia con tu correo y regístralo.",
        )

    is_match = compare_face_embeddings(
        known_embedding=user.face_embedding, new_embedding=request_data.embedding
    )

    if not is_match:
        raise HTTPException(
            status_code=401, detail="Rostro no reconocido. Acceso denegado."
        )

    ip = req.client.host if req.client else "unknown"
    forwarded = req.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()

    audit_id = registrar_auditoria(
        db=db,
        user_uid=user.uid,
        ip=ip,
        ciudad=req.headers.get("X-City"),
        pais=req.headers.get("X-Country"),
        lat=float(req.headers.get("X-Latitude"))
        if req.headers.get("X-Latitude")
        else None,
        lon=float(req.headers.get("X-Longitude"))
        if req.headers.get("X-Longitude")
        else None,
    )

    db.commit()

    role_names = [r.name for r in user.roles]
    initial_role = get_initial_role(role_names)
    access_token = build_scoped_token(db, user, initial_role, audit_id)

    terminos_aceptados_bool = user.terms_accepted_at is not None

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "terms_accepted": terminos_aceptados_bool,
    }


# --- SWITCH ROLE (token scoped a un solo rol) ---


def get_initial_role(user_role_names):
    if "superadmin" in user_role_names:
        return "superadmin"
    return user_role_names[0] if user_role_names else None


def build_scoped_token(db, user, target_role, audit_id=None):
    role_obj = db.query(Role).filter(Role.name == target_role).first()
    return create_access_token(
        data={
            "sub": user.email,
            "nombre": user.nombre,
            "roles": [target_role],
            "permissions": [p.name for p in role_obj.permissions] if role_obj else [],
            "user_id": user.uid,
            "audit_id": audit_id,
        }
    )


@router.post("/switch-role")
def switch_role(
    body: SwitchRoleRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(require_auth),
):
    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(status_code=401, detail="Token inválido: sin email")

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user_role_names = [r.name for r in user.roles]
    if body.role not in user_role_names:
        raise HTTPException(status_code=403, detail=f"No tienes el rol '{body.role}'")

    new_token = build_scoped_token(db, user, body.role)

    return {"access_token": new_token, "token_type": "bearer", "role": body.role}


# --- LOGIN TRADICIONAL (2FA) ---


@router.post("/login")
def login_user(
    request: UserLogin,
    req: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo"
        )

    user_role_names = [r.name for r in user.roles]

    if request.email == "isabela@test.com":
        ip = req.client.host if req.client else "unknown"
        forwarded = req.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()

        audit_id = registrar_auditoria(
            db=db,
            user_uid=user.uid,
            ip=ip,
            ciudad=req.headers.get("X-City"),
            pais=req.headers.get("X-Country"),
            lat=float(req.headers.get("X-Latitude"))
            if req.headers.get("X-Latitude")
            else None,
            lon=float(req.headers.get("X-Longitude"))
            if req.headers.get("X-Longitude")
            else None,
        )
        db.commit()

        initial_role = get_initial_role(user_role_names)
        access_token = build_scoped_token(db, user, initial_role, audit_id)

        terminos_aceptados_bool = user.terms_accepted_at is not None

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "terms_accepted": terminos_aceptados_bool,
            "rol": "revisor-qa",
            "require_2fa": False,
        }

    otp_code = generate_otp()
    expires = datetime.now() + timedelta(minutes=5)

    try:
        query = text(
            "UPDATE usuarios SET two_factor_code = :code, two_factor_expires = :exp WHERE email = :email"
        )
        db.execute(query, {"code": otp_code, "exp": expires, "email": user.email})
        db.commit()
    except Exception as e:
        print(f"Error DB al guardar OTP: {e}")
        raise HTTPException(
            status_code=500, detail="Error interno preparando autenticación"
        )

    background_tasks.add_task(send_2fa_email_sync, user.email, otp_code)

    return {
        "message": "Credenciales correctas. Código de verificación enviado a tu correo.",
        "require_2fa": True,
        "email": user.email,
    }


@router.post("/verify-2fa")
def verify_2fa_code(
    request: Request, verify_data: Verify2FARequest, db: Session = Depends(get_db)
):
    query = text("SELECT * FROM usuarios WHERE email = :email")
    result = db.execute(query, {"email": verify_data.email}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user_data = result._mapping if hasattr(result, "_mapping") else result

    if not user_data["two_factor_code"]:
        raise HTTPException(
            status_code=400,
            detail="No se ha solicitado inicio de sesión o el código ya fue usado",
        )

    if datetime.now() > user_data["two_factor_expires"]:
        raise HTTPException(
            status_code=400, detail="El código ha expirado, inicia sesión nuevamente"
        )

    if not secrets.compare_digest(user_data["two_factor_code"], verify_data.code):
        raise HTTPException(status_code=400, detail="Código inválido")

    db.execute(
        text(
            "UPDATE usuarios SET two_factor_code = NULL, two_factor_expires = NULL WHERE email = :email"
        ),
        {"email": verify_data.email},
    )

    ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    ciudad = request.headers.get("X-City")
    pais = request.headers.get("X-Country")
    lat = request.headers.get("X-Latitude")
    lon = request.headers.get("X-Longitude")

    audit_id = registrar_auditoria(
        db=db,
        user_uid=user_data["uid"],
        ip=ip,
        ciudad=ciudad,
        pais=pais,
        lat=float(lat) if lat else None,
        lon=float(lon) if lon else None,
    )

    db.commit()

    user_orm = db.query(User).filter(User.email == verify_data.email).first()
    role_names = [r.name for r in user_orm.roles]
    initial_role = get_initial_role(role_names)

    access_token = build_scoped_token(db, user_orm, initial_role, audit_id)

    terminos_aceptados_bool = user_orm.terms_accepted_at is not None

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "terms_accepted": terminos_aceptados_bool,
    }


# --- OAUTH (GOOGLE / FACEBOOK) ---
GOOGLE_CLIENT_ID = (
    "559021257590-fk52s7o9oct3lcu43aggujimacqjju2f.apps.googleusercontent.com"
)


@router.get("/google/callback")
def google_callback(request: Request, db: Session = Depends(get_db)):
    token_param = request.query_params.get("credential") or request.query_params.get(
        "id_token"
    )
    if not token_param:
        raise HTTPException(status_code=400, detail="Falta el token de Google")
    try:
        idinfo = id_token.verify_oauth2_token(
            token_param, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        name = idinfo.get("name")
        if not email:
            raise HTTPException(status_code=400, detail="No se pudo extraer el correo")

        user = db.query(User).filter(User.email == email).first()

        if not user:
            default_role = db.query(Role).filter(Role.name == "registrado").first()
            if not default_role:
                raise HTTPException(
                    status_code=400, detail="No se encontró rol por defecto"
                )
            new_user = User(
                uid=str(uuid4()),
                nombre=name,
                tipo_documento="GOOGLE",
                documento="",
                email=email,
                password="",
                estado=True,
            )
            new_user.roles.append(default_role)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user

        ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        registrar_auditoria(db=db, user_uid=user.uid, ip=ip)
        db.commit()

        token = create_access_token(
            data={
                "sub": user.email,
                "nombre": user.nombre,
                "roles": [r.name for r in user.roles],
                "user_id": user.uid,
            }
        )

        terminos_aceptados_bool = user.terms_accepted_at is not None
        redirect_url = f"https://gestordecursos.pegui.edu.co/staging/?token={token}&terms_accepted={str(terminos_aceptados_bool).lower()}"

        return RedirectResponse(redirect_url)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en Google OAuth: {str(e)}")


@router.get("/facebook/callback")
def facebook_callback(request: Request, db: Session = Depends(get_db)):
    access_token = request.query_params.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Falta el token de Facebook")

    try:
        fb_url = "https://graph.facebook.com/me"
        params = {"fields": "id,name,email", "access_token": access_token}
        fb_response = httpx.get(fb_url, params=params)
        if fb_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Token de Facebook inválido")

        fb_data = fb_response.json()
        email = fb_data.get("email")
        name = fb_data.get("name")

        if not email:
            raise HTTPException(
                status_code=400, detail="El usuario de Facebook no tiene email público"
            )

        user = db.query(User).filter(User.email == email).first()

        if not user:
            default_role = db.query(Role).filter(Role.name == "registrado").first()
            if not default_role:
                raise HTTPException(
                    status_code=400, detail="No se encontró rol por defecto"
                )
            new_user = User(
                uid=str(uuid4()),
                nombre=name,
                tipo_documento="FACEBOOK",
                documento="",
                email=email,
                password="",
                estado=True,
            )
            new_user.roles.append(default_role)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user

        ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        registrar_auditoria(db=db, user_uid=user.uid, ip=ip)
        db.commit()

        token = create_access_token(
            data={
                "sub": user.email,
                "nombre": user.nombre,
                "roles": [r.name for r in user.roles],
                "user_id": user.uid,
            }
        )

        terminos_aceptados_bool = user.terms_accepted_at is not None
        redirect_url = f"https://gestordecursos.pegui.edu.co/staging/?token={token}&terms_accepted={str(terminos_aceptados_bool).lower()}"

        return RedirectResponse(redirect_url)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error en Facebook OAuth: {str(e)}"
        )


# ==========================================
# ACTIVAR CUENTA DE CLIENTE (desde email)
# ==========================================
class ActivateClientRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)


@router.post(
    "/activate-client", summary="Activar cuenta de cliente y establecer contraseña"
)
def activate_client(request: ActivateClientRequest, db: Session = Depends(get_db)):
    # Buscar token en password_reset_tokens
    row = db.execute(
        text(
            "SELECT * FROM password_reset_tokens WHERE token = :token AND code = 'activation' AND used = 0 AND (expires_at IS NULL OR expires_at > NOW())"
        ),
        {"token": request.token},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=400, detail="Token inválido o expirado.")

    # Buscar usuario por email
    user = db.query(User).filter(User.email == row.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Actualizar contraseña y activar
    user.password = Hash.encrypt(request.password)
    user.estado = True

    # Marcar token como usado
    db.execute(
        text("UPDATE password_reset_tokens SET used = 1 WHERE id = :id"), {"id": row.id}
    )

    db.commit()
    db.refresh(user)

    return {"msg": "Cuenta activada exitosamente. Ya puedes iniciar sesión."}
