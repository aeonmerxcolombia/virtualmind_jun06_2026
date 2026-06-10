import os
import aiosmtplib
from email.message import EmailMessage
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User


def get_email_config():
    return {
        "hostname": os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        "port": int(os.getenv("MAIL_PORT", 587)),
        "username": os.getenv("MAIL_USERNAME"),
        "password": os.getenv("MAIL_PASSWORD"),
        "start_tls": True,
    }


async def send_email(
    to: str | List[str],
    subject: str,
    body: str,
    html: Optional[str] = None
) -> bool:
    config = get_email_config()

    if not config["username"] or not config["password"]:
        print("Email not configured - missing credentials")
        return False

    msg = EmailMessage()
    msg["From"] = f"{os.getenv('MAIL_FROM_NAME', 'VirtualMind')} <{config['username']}>"
    msg["To"] = to if isinstance(to, str) else ", ".join(to)
    msg["Subject"] = subject

    if html:
        msg.set_content(body)
        msg.add_alternative(html, subtype="html")
    else:
        msg.set_content(body)

    try:
        await aiosmtplib.send(
            msg,
            hostname=config["hostname"],
            port=config["port"],
            username=config["username"],
            password=config["password"],
            start_tls=config.get("start_tls", True)
        )
        print(f"Email sent successfully to {to}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def get_user_email(db: Session, uid: str) -> Optional[str]:
    user = db.query(User).filter(User.uid == uid).first()
    return user.email if user else None


def get_users_emails(db: Session, uids: List[str]) -> List[str]:
    users = db.query(User).filter(User.uid.in_(uids)).all()
    return [u.email for u in users if u.email]


async def notify_project_created(db: Session, project_name: str, client_id: str):
    email = get_user_email(db, client_id)
    if not email:
        return False

    subject = "Nuevo Proyecto Creado"
    body = f"""Hola,

Se ha creado un nuevo proyecto en VirtualMind:

Proyecto: {project_name}
Fecha: {project_name}

Por favor ingresa al sistema para más detalles.

Saludos,
Equipo VirtualMind"""

    return await send_email(email, subject, body)


async def notify_task_created(
    db: Session,
    task_title: str,
    project_name: str,
    asignado: Optional[str] = None,
    seguidores: Optional[List[str]] = None
):
    recipients = []

    if asignado:
        email = get_user_email(db, asignado)
        if email:
            recipients.append(email)

    if seguidores:
        followers_emails = get_users_emails(db, seguidores)
        recipients.extend(followers_emails)

    if not recipients:
        return False

    subject = f"Nueva Tarea Asignada: {task_title}"
    body = f"""Hola,

Se ha creado una nueva tarea en VirtualMind:

Tarea: {task_title}
Proyecto: {project_name}
{'Asignado a: ' + asignado if asignado else ''}

Por favor ingresa al sistema para más detalles.

Saludos,
Equipo VirtualMind"""

    return await send_email(recipients, subject, body)


async def notify_study_plan_created(
    db: Session,
    plan_nombre: str,
    proyecto_nombre: str,
    creador_id: str
):
    """Notificar cuando se crea un plan de estudio."""
    email = get_user_email(db, creador_id)
    if not email:
        return False

    subject = f"Plan de Estudio Creado: {plan_nombre}"
    body = f"""Hola,

Se ha creado un nuevo plan de estudio en VirtualMind:

Plan: {plan_nombre}
Proyecto: {proyecto_nombre}

Por favor ingresa al sistema para más detalles.

Saludos,
Equipo VirtualMind"""

    return await send_email(email, subject, body)


# ==========================================
# NUEVA FUNCIÓN AÑADIDA PARA COMPARTIR ARCHIVOS DE DRIVE
# ==========================================
async def notify_file_shared(
    db: Session,
    archivo_nombre: str,
    destinatario_email: str,
    remitente_id: str,
    mensaje_opcional: str = ""
):
    """Notificar cuando un usuario comparte un archivo de Drive."""
    
    # Obtenemos el correo de quien comparte para mostrarlo en el mensaje
    remitente_email = get_user_email(db, remitente_id) or "Un colega"

    subject = f"Han compartido un curso contigo: {archivo_nombre}"
    
    mensaje_extra = f'\nMensaje de {remitente_email}: "{mensaje_opcional}"\n' if mensaje_opcional else ''
    
    body = f"""Hola,

El usuario {remitente_email} te ha compartido el archivo "{archivo_nombre}" en el Drive de VirtualMind 360.
{mensaje_extra}
Por favor ingresa al sistema para verlo o editarlo.

Saludos,
Equipo VirtualMind"""

    return await send_email(destinatario_email, subject, body)


async def notify_videollamada(
    db: Session,
    destinatario_uid: str,
    remitente_uid: str,
    url_videollamada: str
):
    """Notificar por correo cuando se envía una invitación a videollamada."""
    destinatario_email = get_user_email(db, destinatario_uid)
    remitente_email = get_user_email(db, remitente_uid)
    
    if not destinatario_email:
        return False
    
    if not remitente_email:
        remitente_email = "Un usuario"

    subject = "Invitación a Videollamada - VirtualMind"
    body = f"""Hola,

{remitente_email} te ha enviado una invitación a una videollamada.

Haz clic en el siguiente enlace para unirte:
{url_videollamada}

Saludos,
Equipo VirtualMind"""

    return await send_email(destinatario_email, subject, body)
