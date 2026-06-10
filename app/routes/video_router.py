import os
import uuid
import datetime
import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.sesion_video import SesionVideo
from app.schemas.video_schema import VideoSessionCreate, VideoSessionRead
from app.auth.jwt_handler import decodeJWT  # Importación de tu validador de tokens existente

# CONFIGURACIÓN SEGURA DE JITSI JAAS (8x8)
APP_ID = "vpaas-magic-cookie-d45c8107f37a4d70a21bf1932daaf52d"
JITSI_KEY_ID = "vpaas-magic-cookie-d45c8107f37a4d70a21bf1932daaf52d/b2bd13"
RUTA_LLAVE_PRIVADA = "/home/ubuntu/backend/app/certs/jitsi_private_key.pem"

router = APIRouter(prefix="/video", tags=["videollamada"])

def generar_token_jitsi(room_name: str, nombre_usuario: str, email_usuario: str) -> str:
    """
    Genera un token JWT firmado asimétricamente usando RS256 con el Key ID (kid)
    requerido por los servidores de autenticación de Jitsi (JaaS).
    """
    try:
        # Cargar la llave privada (.pem) guardada en /certs/
        with open(RUTA_LLAVE_PRIVADA, "r") as f:
            private_key_pem = f.read()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Llave privada Jitsi no encontrada en la ruta especificada: {RUTA_LLAVE_PRIVADA}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al leer la llave privada Jitsi: {str(e)}"
        )

    # Estructura del Payload requerida por 8x8 JaaS
    payload = {
        "aud": "jitsi",
        "iss": "chat",
        "sub": APP_ID,
        "room": room_name,
        "context": {
            "user": {
                "name": nombre_usuario,
                "email": email_usuario,
                "moderator": True
            }
        },
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }

    # Cabeceras obligatorias conteniendo el Key ID (kid) de tu API Key de Jitsi (JaaS)
    headers = {
        "kid": JITSI_KEY_ID,
        "typ": "JWT"
    }

    # Firma asimétrica estricta usando RS256
    return jwt.encode(payload, private_key_pem, algorithm="RS256", headers=headers)


@router.post("/iniciar", response_model=VideoSessionRead)
async def iniciar_videollamada(
    data: VideoSessionCreate, 
    db: Session = Depends(get_db)
):
    """
    Registra una nueva reunión en MySQL y genera el token de acceso para el creador.
    """
    try:
        # Generar un identificador de sala seguro y único
        room_id = f"vm_{uuid.uuid4().hex}"
        
        # Registrar la sesión en la base de datos MySQL con estado 'waiting'
        nueva_sesion = SesionVideo(
            room_name=room_id,
            creador_uid=data.mi_uid,
            participante_uid=data.destinatario_uid,
            status='waiting'
        )
        
        db.add(nueva_sesion)
        db.commit()
        db.refresh(nueva_sesion)
        
        # Firmar el JWT usando RS256 para el usuario de origen
        token = generar_token_jitsi(room_id, data.mi_nombre, data.mi_email)
        
        return {
            "url": f"https://8x8.vc/{APP_ID}/{room_id}",
            "token": token,
            "room_name": room_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al registrar la sesión de video: {str(e)}"
        )


@router.get("/entrar/{room_name}")
async def entrar_videollamada(
    room_name: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint para participantes y reingreso del creador: valida que el usuario 
    pertenezca a la sesión registrada en MySQL antes de generarle el JWT de acceso con RS256.
    """
    # 1. Intentar recuperar el usuario inyectado por tu middleware auth_middleware en main.py
    user_state = getattr(request.state, "user", None)
    
    # === MECANISCO DE RESILIENCIA (FALLBACK DE AUTODESCIFRADO) ===
    # Si la ruta fue marcada como pública, el middleware no procesará el token.
    # Extraemos y decodificamos el token de forma manual para evitar fallos de autenticación.
    if not user_state:
        auth_header = request.headers.get("Authorization")
        token = auth_header.replace("Bearer ", "") if auth_header else None
        
        if not token:
            token = request.query_params.get("token")
            
        if token:
            try:
                user_state = decodeJWT(token)
            except Exception:
                pass  # Dejar pasar para que retorne el 401 controlado de abajo

    if not user_state:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error de autenticación. Sesión de usuario no válida o expirada."
        )

    # Capturamos de forma segura el UID y datos del token descifrado
    user_uid = user_state.get("user_id") or user_state.get("sub")
    user_name = user_state.get("nombre") or user_state.get("sub", "Usuario")
    user_email = user_state.get("sub", "")

    # 2. Consultar en MySQL si el usuario es el creador o el invitado de esta sala
    sesion = db.query(SesionVideo).filter(
        SesionVideo.room_name == room_name,
        SesionVideo.status != 'finished'
    ).first()

    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sala de videoconferencia no existe o ya ha finalizado."
        )

    # Validar permisos de acceso (solo creador o participante asignado pueden entrar)
    if sesion.creador_uid != user_uid and sesion.participante_uid != user_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. No perteneces a esta reunión."
        )

    # 3. Si es el primer reingreso del invitado, actualizar el estado de la sala a activa
    if sesion.status == 'waiting' and user_uid == sesion.participante_uid:
        sesion.status = 'active'
        db.commit()

    # 4. Generar y entregar el token Jitsi firmado con RS256 de forma asimétrica
    token = generar_token_jitsi(room_name, user_name, user_email)
    
    return {"token": token}
