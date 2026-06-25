# app/routes/client_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import uuid, secrets, os, smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

from app.database.db import get_db
from app.models.user import User
from app.models.role import Role
from app.models.client_profile import ClientProfile

# Importar esquemas - AÑADIMOS UserStatusUpdate
from app.schemas.user_schema import UserCreate, UserOut, UserUpdate, UserStatusUpdate
from app.schemas.client_schema import FullClientCreate

# Importar utilidades de seguridad
from app.auth.hashing import Hash

# Importar los routers existentes para perfiles y documentos
from app.routes import client_profile_router, client_document_router

# Crear el router principal para clientes
router = APIRouter(
    prefix="/clients",
    tags=["Clientes"]
)

# Incluir los routers secundarios
router.include_router(client_profile_router.router, prefix="/profiles", tags=["Clientes"])
router.include_router(client_document_router.router, prefix="/documents", tags=["Clientes"])


# --------------------------
# ### --- CREAR CLIENTE COMPLETO --- ###
# --------------------------
@router.post("/", response_model=UserOut, summary="Crear un nuevo cliente con su perfil completo")
def create_client(
    client_data: FullClientCreate,
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo cliente (cuenta de usuario y perfil de cliente).
    - Si el email ya existe, solo crea/actualiza el perfil de cliente.
    - El documento debe ser único para nuevos usuarios.
    - La cuenta se crea como inactiva (estado=False).
    - Se asigna automáticamente el rol 'cliente'.
    """
    existing_user = db.query(User).filter(User.email == client_data.email).first()
    
    if existing_user:
        # El usuario ya existe - solo crear/actualizar el perfil
        client_role = db.query(Role).filter(Role.name == "cliente").first()
        if not client_role:
            raise HTTPException(status_code=500, detail="Rol 'cliente' no encontrado.")
        
        # Agregar rol de cliente si no lo tiene
        if client_role not in existing_user.roles:
            existing_user.roles.append(client_role)
        
        # Verificar si ya tiene perfil de cliente
        profile_dict = client_data.profile.model_dump()
        existing_profile = db.query(ClientProfile).filter(ClientProfile.user_id == existing_user.uid).first()
        
        if existing_profile:
            # Actualizar perfil existente
            for key, value in profile_dict.items():
                if hasattr(existing_profile, key):
                    setattr(existing_profile, key, value)
        else:
            # Crear nuevo perfil para el usuario existente
            db_profile = ClientProfile(
                id=str(uuid.uuid4()),
                user_id=existing_user.uid,
                **profile_dict
            )
            db.add(db_profile)
        
        try:
            db.commit()
            db.refresh(existing_user)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al guardar el perfil: {e}")
        
        return existing_user
    
    # Nuevo usuario - crear usuario y perfil
    if db.query(User).filter(User.documento == client_data.documento).first():
        raise HTTPException(status_code=400, detail="Documento ya registrado.")

    user_uid = str(uuid.uuid4())
    profile_info = client_data.profile

    nombre_completo_usuario = " ".join(filter(None, [
        profile_info.pnombre,
        profile_info.snombre,
        profile_info.papellido,
        profile_info.sapellido
    ]))

    # Generar token de activación (sin contraseña, se envía link por email)
    activation_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=48)

    # Almacenar token en password_reset_tokens con code='activation'
    db.execute(
        text("INSERT INTO password_reset_tokens (email, token, code, expires_at, used) VALUES (:email, :token, 'activation', :expires, 0)"),
        {"email": client_data.email, "token": activation_token, "expires": expires_at}
    )

    # Contraseña temporal (usuario debe activar cuenta para poder acceder)
    placeholder_hash = Hash.encrypt(f"Pending_{uuid.uuid4().hex[:16]}")

    db_user = User(
        uid=user_uid,
        email=client_data.email,
        nombre=nombre_completo_usuario or client_data.nombre,
        tipo_documento=client_data.tipo_documento,
        documento=client_data.documento,
        password=placeholder_hash,
        estado=False,
    )

    client_role = db.query(Role).filter(Role.name == "cliente").first()
    if not client_role:
        raise HTTPException(status_code=500, detail="Rol 'cliente' no encontrado.")
    db_user.roles.append(client_role)

    profile_dict = profile_info.model_dump()
    db_profile = ClientProfile(
        id=str(uuid.uuid4()),
        user_id=db_user.uid,
        **profile_dict
    )

    db.add(db_user)
    db.add(db_profile)

    try:
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar en la base de datos: {e}")

    try:
        _send_activation_email(client_data.email, activation_token)
    except Exception as e:
        print(f"Error enviando email de activación: {e}")

    return db_user

# --------------------------
# ### --- LISTAR CLIENTES --- ###
# --------------------------
@router.get("/", response_model=List[UserOut], summary="Listar clientes")
def list_clients(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[bool] = None,
    nombre: Optional[str] = None,
    email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    client_role = db.query(Role).filter(Role.name == "cliente").first()
    if not client_role:
        return []

    query = db.query(User).join(User.roles).filter(Role.id == client_role.id)

    if estado is not None:
        query = query.filter(User.estado == estado)
    if nombre:
        query = query.filter(User.nombre.ilike(f"%{nombre}%"))
    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))

    clients = query.offset(skip).limit(limit).all()
    return clients

# --------------------------
# ### --- OBTENER UN CLIENTE --- ###
# --------------------------
@router.get("/{user_id}", response_model=UserOut, summary="Obtener detalles de un cliente")
def get_client(user_id: str, db: Session = Depends(get_db)):
    client_role = db.query(Role).filter(Role.name == "cliente").first()
    if not client_role:
        raise HTTPException(status_code=404, detail="Rol 'cliente' no encontrado.")
    
    db_user = db.query(User).join(User.roles).filter(User.uid == user_id, Role.id == client_role.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    return db_user

# --------------------------
# ### --- ACTUALIZAR DATOS GENERALES DE UN CLIENTE --- ###
# --------------------------
@router.patch("/{user_id}", response_model=UserOut, summary="Actualizar datos generales de un cliente")
def update_client(
    user_id: str,
    client_update: UserUpdate,
    db: Session = Depends(get_db)
):
    client_role = db.query(Role).filter(Role.name == "cliente").first()
    if not client_role:
        raise HTTPException(status_code=404, detail="Rol 'cliente' no encontrado.")
    
    db_user = db.query(User).join(User.roles).filter(User.uid == user_id, Role.id == client_role.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    update_data = client_update.dict(exclude_unset=True)
    update_data.pop("role_ids", None) # No permitir cambiar roles desde esta ruta

    if "password" in update_data and update_data["password"]:
        update_data["password"] = Hash.encrypt(update_data["password"])
    elif "password" in update_data:
        update_data.pop("password", None)

    for key, value in update_data.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

# --------------------------------------------------------------------------
# ### --- ✅ NUEVA RUTA PARA ACTIVAR Y DESACTIVAR ESTADO --- ###
# --------------------------------------------------------------------------
@router.patch("/{user_id}/status", response_model=UserOut, summary="Activar o desactivar un cliente")
def update_client_status(
    user_id: str,
    status_data: UserStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza únicamente el estado (activo/inactivo) de un cliente específico.
    """
    client_role = db.query(Role).filter(Role.name == "cliente").first()
    if not client_role:
        raise HTTPException(status_code=404, detail="Rol 'cliente' no encontrado.")
    
    db_user = db.query(User).join(User.roles).filter(User.uid == user_id, Role.id == client_role.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    db_user.estado = status_data.estado
    db.commit()
    db.refresh(db_user)
    return db_user

# ==========================================
# EMAIL DE ACTIVACIÓN
# ==========================================
def _send_activation_email(email_to: str, token: str):
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "VirtualMind")

    activation_link = f"https://gestordecursos.pegui.edu.co/activate-account.html?token={token}"

    message = EmailMessage()
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    message["To"] = email_to
    message["Subject"] = "Activa tu cuenta en VirtualMind"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px; max-width: 500px;">
        <h2 style="color: #333;">Bienvenido a VirtualMind</h2>
        <p>Hola,</p>
        <p>Tu cuenta ha sido creada exitosamente. Para poder acceder a la plataforma, debes activar tu cuenta creando una contraseña segura.</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{activation_link}" style="background-color: #4A90E2; color: white; padding: 14px 28px; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; display: inline-block;">Activar mi cuenta</a>
        </p>
        <p style="font-size: 12px; color: #777;">Este enlace expira en 48 horas. Si no solicitaste esta cuenta, ignora este mensaje.</p>
        <p style="font-size: 12px; color: #777;">Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:<br>{activation_link}</p>
    </div>
    """
    message.set_content(f"Activa tu cuenta en VirtualMind: {activation_link}")
    message.add_alternative(html_content, subtype='html')

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(message)
