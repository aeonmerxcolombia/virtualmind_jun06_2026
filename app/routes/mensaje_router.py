import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import uuid4

from app.database.db import get_db, SessionLocal
from app.auth.jwt_handler import verify_token
from app.models.mensaje import Mensaje
from app.schemas.mensaje_schema import MensajeCreate, MensajeOut
from app.services.email_service import notify_videollamada
from app.services.log_service import crear_notificacion

router = APIRouter(
    prefix="/mensajes",
    tags=["Mensajes"]
)

@router.post("/", response_model=MensajeOut, status_code=status.HTTP_201_CREATED)
def enviar_mensaje(
    data: MensajeCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    mensaje = Mensaje(
        id=str(uuid4()),
        contenido=data.contenido,
        remitente_uid=token_data["user_id"],
        destinatario_uid=data.destinatario_uid
    )
    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)
    
    # Si es una invitación a videollamada, enviar correo en background
    if "videollamada" in data.contenido.lower() and "http" in data.contenido:
        # Extraer la URL de la videollamada
        import re
        url_match = re.search(r'(https?://[^\s]+)', data.contenido)
        url_videollamada = url_match.group(1) if url_match else ""
        
        if url_videollamada:
            # Obtener nombre del remitente para la notificación
            from app.models.user import User
            remitente = db.query(User).filter(User.uid == token_data["user_id"]).first()
            nombre_remitente = remitente.nombre if remitente and remitente.nombre else "Un usuario"
            
            # Enviar correo en background
            background_tasks.add_task(
                notify_videollamada,
                db,
                data.destinatario_uid,
                token_data["user_id"],
                url_videollamada
            )
            
            # Crear notificación interna
            crear_notificacion(
                db,
                usuario_id=data.destinatario_uid,
                tipo_evento="videollamada",
                descripcion=f"💬 {nombre_remitente} te ha enviado una invitación a videollamada. Haz clic para unirte."
            )
    
    return mensaje

@router.get("/inbox", response_model=list[MensajeOut])
def recibir_mis_mensajes(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    return db.query(Mensaje).filter(
        Mensaje.destinatario_uid == token_data["user_id"]
    ).order_by(Mensaje.timestamp.desc()).all()

@router.get("/enviados", response_model=list[MensajeOut])
def mensajes_enviados(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    return db.query(Mensaje).filter(
        Mensaje.remitente_uid == token_data["user_id"]
    ).order_by(Mensaje.timestamp.desc()).all()

@router.delete("/{mensaje_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_mensaje(
    mensaje_id: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    mensaje = db.query(Mensaje).filter(Mensaje.id == mensaje_id).first()
    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    # Solo puede borrar si es el remitente o destinatario
    if mensaje.remitente_uid != token_data["user_id"] and mensaje.destinatario_uid != token_data["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para borrar este mensaje")

    db.delete(mensaje)
    db.commit()

@router.get("/conversacion/{otro_uid}", response_model=list[MensajeOut])
def conversacion_con_usuario(
    otro_uid: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    """
    Obtener todos los mensajes entre el usuario actual y otro usuario (enviados y recibidos).
    """
    mi_uid = token_data["user_id"]
    return db.query(Mensaje).filter(
        ((Mensaje.remitente_uid == mi_uid) & (Mensaje.destinatario_uid == otro_uid)) |
        ((Mensaje.remitente_uid == otro_uid) & (Mensaje.destinatario_uid == mi_uid))
    ).order_by(Mensaje.timestamp.asc()).all()

@router.get("/stream")
async def stream_mensajes(
    otro_uid: str,
    token_data: dict = Depends(verify_token)
):
    """
    SSE endpoint for real-time chat messages.
    Polls every 2 seconds for new messages, sends ping every 30 seconds.
    Timeout: 300 seconds (5 minutes).
    """
    uid = token_data["user_id"]

    async def event_generator():
        last_check = datetime.utcnow()
        ping_count = 0
        try:
            while True:
                db = SessionLocal()
                try:
                    nuevos = db.query(Mensaje).filter(
                        ((Mensaje.remitente_uid == uid) & (Mensaje.destinatario_uid == otro_uid)) |
                        ((Mensaje.remitente_uid == otro_uid) & (Mensaje.destinatario_uid == uid)),
                        Mensaje.timestamp > last_check
                    ).order_by(Mensaje.timestamp.asc()).all()

                    for msg in nuevos:
                        data = {
                            "id": msg.id,
                            "contenido": msg.contenido,
                            "remitente_uid": msg.remitente_uid,
                            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                        }
                        yield f"data: {json.dumps(data)}\n\n"

                    if nuevos:
                        last_check = nuevos[-1].timestamp
                finally:
                    db.close()

                ping_count += 1
                if ping_count >= 15:
                    yield f"event: ping\ndata: {json.dumps({'time': datetime.utcnow().isoformat()})}\n\n"
                    ping_count = 0

                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

