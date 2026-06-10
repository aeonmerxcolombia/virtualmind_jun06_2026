from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime

from app.database.db import get_db
from app.models.tarea import Tarea
from app.models.vencimiento import SolicitudAmpliacion
from app.services.vencimiento_service import verificar_vencimientos
from app.services.log_service import crear_notificacion
from app.services.email_service import get_user_email, send_email
from app.auth.jwt_handler import verify_token

router = APIRouter(tags=["vencimientos"])


@router.post("/vencimientos/verificar")
async def trigger_verificar_vencimientos(db: Session = Depends(get_db)):
    enviadas = await verificar_vencimientos(db)
    return {"ok": True, "notificaciones_enviadas": enviadas}

@router.get("/vencimientos/verificar")
async def trigger_verificar_vencimientos_get(db: Session = Depends(get_db)):
    enviadas = await verificar_vencimientos(db)
    return {"ok": True, "notificaciones_enviadas": enviadas}


@router.post("/tareas/{tarea_id}/solicitar-ampliacion")
async def solicitar_ampliacion(
    tarea_id: int,
    fecha_solicitada: str = Form(...),
    razon: str = Form(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if not tarea.fecha_entrega:
        raise HTTPException(status_code=400, detail="La tarea no tiene fecha de entrega")

    user_id = token_data.get("user_id")

    try:
        nueva_fecha = date.fromisoformat(fecha_solicitada)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido (YYYY-MM-DD)")

    if nueva_fecha <= tarea.fecha_entrega:
        raise HTTPException(
            status_code=400,
            detail="La fecha solicitada debe ser posterior a la fecha actual de entrega",
        )

    solicitud = SolicitudAmpliacion(
        tarea_id=tarea_id,
        usuario_id=user_id,
        fecha_actual=tarea.fecha_entrega,
        fecha_solicitada=nueva_fecha,
        razon=razon,
        estado="pendiente",
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)

    crear_notificacion(
        db=db,
        usuario_id=user_id,
        tipo_evento="ampliacion_solicitada",
        descripcion=f"📅 Solicitaste ampliación para '{tarea.titulo}' hasta {nueva_fecha}",
    )

    return {
        "ok": True,
        "solicitud_id": solicitud.id,
        "mensaje": "Solicitud de ampliación enviada correctamente",
    }


@router.get("/tareas/solicitudes-ampliacion")
async def listar_solicitudes(
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    query = db.query(SolicitudAmpliacion, Tarea).join(
        Tarea, SolicitudAmpliacion.tarea_id == Tarea.id
    )
    if estado:
        query = query.filter(SolicitudAmpliacion.estado == estado)
    resultados = query.order_by(SolicitudAmpliacion.fecha_creacion.desc()).all()

    return [
        {
            "id": s.id,
            "tarea_id": s.tarea_id,
            "tarea_titulo": t.titulo,
            "usuario_id": s.usuario_id,
            "fecha_actual": str(s.fecha_actual),
            "fecha_solicitada": str(s.fecha_solicitada),
            "razon": s.razon,
            "estado": s.estado,
            "respuesta_admin": s.respuesta_admin,
            "fecha_resolucion": str(s.fecha_resolucion) if s.fecha_resolucion else None,
            "fecha_creacion": str(s.fecha_creacion),
        }
        for s, t in resultados
    ]


@router.put("/tareas/solicitudes-ampliacion/{solicitud_id}")
async def resolver_solicitud(
    solicitud_id: int,
    estado: str = Form(...),
    respuesta_admin: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    roles = token_data.get("roles", [])
    roles_permitidos = ["superadmin", "admin", "coordinador", "cliente"]
    if not any(r in roles for r in roles_permitidos):
        raise HTTPException(
            status_code=403,
            detail="Solo superadmin, admin, coordinador o cliente pueden resolver solicitudes",
        )

    solicitud = db.query(SolicitudAmpliacion).filter(
        SolicitudAmpliacion.id == solicitud_id
    ).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if estado not in ("aprobada", "rechazada"):
        raise HTTPException(status_code=400, detail="Estado debe ser 'aprobada' o 'rechazada'")

    admin_id = token_data.get("user_id")
    solicitud.estado = estado
    solicitud.respuesta_admin = respuesta_admin
    solicitud.fecha_resolucion = datetime.utcnow()
    solicitud.resuelto_por = admin_id

    tarea = db.query(Tarea).filter(Tarea.id == solicitud.tarea_id).first()

    if estado == "aprobada" and tarea:
        tarea.fecha_entrega = solicitud.fecha_solicitada

    db.commit()

    if tarea:
        estado_emoji = "✅" if estado == "aprobada" else "❌"
        crear_notificacion(
            db=db,
            usuario_id=solicitud.usuario_id,
            tipo_evento=f"ampliacion_{estado}",
            descripcion=f"{estado_emoji} Solicitud de ampliación para '{tarea.titulo}' fue {estado}",
        )
        email_user = get_user_email(db, solicitud.usuario_id)
        if email_user:
            await send_email(
                to=email_user,
                subject=f"{estado_emoji} Ampliación {estado}: {tarea.titulo}",
                body=f"Tu solicitud de ampliación para la tarea '{tarea.titulo}' fue {estado}.\n"
                + (f"Comentario: {respuesta_admin}\n" if respuesta_admin else "")
                + f"Nueva fecha: {solicitud.fecha_solicitada}\n" if estado == "aprobada" else "",
            )

    return {
        "ok": True,
        "solicitud_id": solicitud.id,
        "estado": estado,
    }
