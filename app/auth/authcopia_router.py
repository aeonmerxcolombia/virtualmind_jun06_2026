# app/auth/auth_router.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import uuid4
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.database.db import SessionLocal
from app.models.user import User
from app.models.role import Role

# --- CAMBIO 1: Importamos el schema 'Token' ---
from app.schemas.user_schema import UserCreate, UserLogin, Token

from app.auth.hashing import Hash
from app.auth.jwt_handler import create_access_token
import httpx


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(request: UserCreate, db: Session = Depends(get_db)):
    # (Tu lógica de registro no cambia)
    # 1. Verificar email único
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    # 2. Validar que todos los role_ids existen
    roles = db.query(Role).filter(Role.id.in_(request.role_ids)).all()
    if len(roles) != len(request.role_ids):
        raise HTTPException(status_code=400, detail="Algún role_id no es válido")
    # 3. Crear usuario y asignar roles
    new_user = User(
        uid=str(uuid4()),
        nombre=request.nombre,
        tipo_documento=request.tipo_documento,
        documento=request.documento,
        email=request.email,
        password=Hash.encrypt(request.password),
        estado=True
        # terms_accepted_at se queda NULL por defecto
    )
    new_user.roles = roles
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "Usuario creado exitosamente", "uid": new_user.uid}


# --- CAMBIO 2: Endpoint de Login modificado ---
@router.post("/login", response_model=Token) # <-- (A) Usamos el nuevo response_model
def login_user(request: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    
    # Validación de usuario y contraseña
    if not user or not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    
    # Validación de estado
    if not user.estado:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Usuario inactivo"
        )

    # (B) Creamos el token de acceso
    access_token = create_access_token(data={
        "sub": user.email,
        "roles": [r.name for r in user.roles],
        "user_id": user.uid
    })

    # (C) Revisamos si los términos fueron aceptados
    terminos_aceptados_bool = user.terms_accepted_at is not None
    
    # (D) Devolvemos el objeto 'Token' completo
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "terms_accepted": terminos_aceptados_bool # <-- ¡El flag para el frontend!
    }

GOOGLE_CLIENT_ID = "559021257590-fk52s7o9oct3lcu43aggujimacqjju2f.apps.googleusercontent.com"

# --- CAMBIO 3: Callbacks de OAuth modificados ---

@router.get("/google/callback")
def google_callback(request: Request, db: Session = Depends(get_db)):
    token_param = request.query_params.get("credential") or request.query_params.get("id_token")
    if not token_param:
        raise HTTPException(status_code=400, detail="Falta el token de Google")
    try:
        idinfo = id_token.verify_oauth2_token(
            token_param,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        name = idinfo.get("name")
        if not email:
            raise HTTPException(status_code=400, detail="No se pudo extraer el correo")
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # (Lógica para crear usuario nuevo...)
            default_role = db.query(Role).filter(Role.name == "registrado").first()
            if not default_role:
                raise HTTPException(status_code=400, detail="No se encontró rol por defecto")
            new_user = User(
                uid=str(uuid4()),
                nombre=name,
                tipo_documento="GOOGLE",
                documento="",
                email=email,
                password="", # Sin password local
                estado=True
            )
            new_user.roles.append(default_role)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user # Asignamos el nuevo usuario
        
        # (A) Creamos el token
        token = create_access_token(data={
            "sub": user.email,
            "roles": [r.name for r in user.roles],
            "user_id": user.uid
        })
        
        # (B) Revisamos los términos (para el usuario existente o el nuevo)
        terminos_aceptados_bool = user.terms_accepted_at is not None
        
        # (C) Añadimos el flag a la URL de redirección
        # Usamos .lower() para que sea 'true' o 'false' en la URL
        redirect_url = f"https://gestordecursos.pegui.edu.co/?token={token}&terms_accepted={str(terminos_aceptados_bool).lower()}"

        return RedirectResponse(redirect_url)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en Google OAuth: {str(e)}")

@router.get("/facebook/callback")
def facebook_callback(request: Request, db: Session = Depends(get_db)):
    access_token = request.query_params.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Falta el token de Facebook")

    try:
        # (Lógica de Facebook...)
        fb_url = "https://graph.facebook.com/me"
        params = {"fields": "id,name,email", "access_token": access_token}
        fb_response = httpx.get(fb_url, params=params)
        if fb_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Token de Facebook inválido")

        fb_data = fb_response.json()
        email = fb_data.get("email")
        name = fb_data.get("name")

        if not email:
            raise HTTPException(status_code=400, detail="El usuario de Facebook no tiene email público")

        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # (Lógica para crear usuario nuevo...)
            default_role = db.query(Role).filter(Role.name == "registrado").first()
            if not default_role:
                raise HTTPException(status_code=400, detail="No se encontró rol por defecto")
            new_user = User(
                uid=str(uuid4()),
                nombre=name,
                tipo_documento="FACEBOOK",
                documento="",
                email=email,
                password="",
                estado=True
            )
            new_user.roles.append(default_role)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user # Asignamos el nuevo usuario

        # (A) Creamos el token
        token = create_access_token(data={
            "sub": user.email,
            "roles": [r.name for r in user.roles],
            "user_id": user.uid
        })
        
        # (B) Revisamos los términos
        terminos_aceptados_bool = user.terms_accepted_at is not None
        
        # (C) Añadimos el flag a la URL de redirección
        redirect_url = f"https://gestordecursos.pegui.edu.co/?token={token}&terms_accepted={str(terminos_aceptados_bool).lower()}"

        return RedirectResponse(redirect_url)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en Facebook OAuth: {str(e)}")
