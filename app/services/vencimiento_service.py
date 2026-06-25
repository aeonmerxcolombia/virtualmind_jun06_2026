from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.tarea import Tarea
from app.models.vencimiento import AlertaVencimiento, SolicitudAmpliacion
from app.services.log_service import crear_notificacion
from app.services.email_service import send_email, get_user_email

DIAS_ALERTA = 2


async def verificar_vencimientos(db: Session):
    hoy = date.today()
    fecha_limite = hoy + timedelta(days=DIAS_ALERTA)

    tareas_proximas = db.query(Tarea).filter(
        and_(
            Tarea.fecha_entrega.isnot(None),
            Tarea.fecha_entrega >= hoy,
            Tarea.fecha_entrega <= fecha_limite,
            Tarea.estado.notin_(["Cerrado", "Resuelto"]),
        )
    ).all()

    notificaciones_enviadas = 0
    for tarea in tareas_proximas:
        creador_id = tarea.creado_por
        dias_restantes = (tarea.fecha_entrega - hoy).days

        # Verificar si ya se envió alerta para esta tarea
        ya_enviado_creador = False
        if creador_id:
            ya_enviado_creador = db.query(AlertaVencimiento).filter(
                AlertaVencimiento.tarea_id == tarea.id,
                AlertaVencimiento.enviado_a == creador_id,
            ).first() is not None

        if creador_id and not ya_enviado_creador:
            desc = f"⏰ La tarea '{tarea.titulo}' vence en {dias_restantes} día(s) ({tarea.fecha_entrega})"
            crear_notificacion(
                db=db,
                usuario_id=creador_id,
                tipo_evento="vencimiento_proximo",
                descripcion=desc,
            )
            # Email al creador
            email = get_user_email(db, creador_id)
            if email:
                await send_email(
                    to=email,
                    subject=f"⏰ Tarea por vencer: {tarea.titulo}",
                    body=f"La tarea '{tarea.titulo}' vence el {tarea.fecha_entrega}.\n\nQuedan {dias_restantes} día(s).\n\nPor favor ingresa al sistema para más detalles.",
                )
            # Registrar alerta
            alerta = AlertaVencimiento(
                tarea_id=tarea.id,
                tipo="recordatorio",
                enviado_a=creador_id,
                dias_antes=dias_restantes,
            )
            db.add(alerta)
            notificaciones_enviadas += 1

        # También notificar al asignado si es diferente del creador
        if tarea.asignado and tarea.asignado != creador_id:
            ya_enviado_asign = db.query(AlertaVencimiento).filter(
                AlertaVencimiento.tarea_id == tarea.id,
                AlertaVencimiento.enviado_a == tarea.asignado,
            ).first() is not None

            if not ya_enviado_asign:
                desc = f"⏰ Tarea '{tarea.titulo}' vence en {dias_restantes} día(s). Fecha: {tarea.fecha_entrega}"
                crear_notificacion(
                    db=db,
                    usuario_id=tarea.asignado,
                    tipo_evento="vencimiento_proximo",
                    descripcion=desc,
                )
                email_asign = get_user_email(db, tarea.asignado)
                if email_asign:
                    await send_email(
                        to=email_asign,
                        subject=f"⏰ Tarea por vencer: {tarea.titulo}",
                        body=f"La tarea '{tarea.titulo}' asignada a ti vence el {tarea.fecha_entrega}.\n\nQuedan {dias_restantes} día(s).\n\nPor favor ingresa al sistema.",
                    )
                alerta2 = AlertaVencimiento(
                    tarea_id=tarea.id,
                    tipo="recordatorio",
                    enviado_a=tarea.asignado,
                    dias_antes=dias_restantes,
                )
                db.add(alerta2)
                notificaciones_enviadas += 1

        # También notificar a vencidos
    tareas_vencidas = db.query(Tarea).filter(
        and_(
            Tarea.fecha_entrega.isnot(None),
            Tarea.fecha_entrega < hoy,
            Tarea.estado.notin_(["Cerrado", "Resuelto"]),
        )
    ).all()

    for tarea in tareas_vencidas:
        creador_id = tarea.creado_por
        ya_alert_vencido = False
        if creador_id:
            ya_alert_vencido = db.query(AlertaVencimiento).filter(
                AlertaVencimiento.tarea_id == tarea.id,
                AlertaVencimiento.enviado_a == creador_id,
                AlertaVencimiento.tipo == "vencido",
            ).first() is not None

        if creador_id and not ya_alert_vencido:
            desc = f"🔴 La tarea '{tarea.titulo}' venció el {tarea.fecha_entrega}"
            crear_notificacion(
                db=db,
                usuario_id=creador_id,
                tipo_evento="tarea_vencida",
                descripcion=desc,
            )
            alerta = AlertaVencimiento(
                tarea_id=tarea.id,
                tipo="vencido",
                enviado_a=creador_id,
                dias_antes=0,
            )
            db.add(alerta)
            notificaciones_enviadas += 1

    db.commit()
    return notificaciones_enviadas
