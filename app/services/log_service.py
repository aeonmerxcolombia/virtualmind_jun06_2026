# app/services/log_service.py

from sqlalchemy.orm import Session
from app.models.log_model import LogAccion
from app.models.user import User
# --- CAMBIOS DE IMPORTACIÓN ---
from typing import Optional, List
from datetime import date, timedelta
# --- FIN CAMBIOS ---

# ---------------------------
# Registro de logs
# ---------------------------
def registrar_log(db: Session, usuario_id: int, tipo_evento: str, descripcion: str):
    """
    Registrar un log en la base de datos.
    """
    nuevo_log = LogAccion(
        usuario_id=usuario_id,
        tipo_evento=tipo_evento,
        descripcion=descripcion
    )
    db.add(nuevo_log)
    db.commit()
    db.refresh(nuevo_log)
    return nuevo_log


# ---------------------------
# Logs globales del sistema
# ---------------------------
def obtener_logs(db: Session, limit: int = 100):
    """
    Obtener los últimos logs del sistema (para admins o auditoría).
    """
    query = db.query(LogAccion, User).join(User, LogAccion.usuario_id == User.uid, isouter=True)
    results = query.order_by(LogAccion.fecha.desc()).limit(limit).all()

    return [
        {
            "id": log.id,
            "usuario_id": log.usuario_id,
            "usuario": user.nombre if user else f"User {log.usuario_id}",
            "tipo_evento": log.tipo_evento,
            "descripcion": log.descripcion,
            "fecha": log.fecha
        }
        for log, user in results
    ]


# ---------------------------
# Notificaciones personales
# ---------------------------
def obtener_notificaciones_usuario(db: Session, usuario_id: int, limit: int = 50):
    """
    Obtener solo las notificaciones/logs de un usuario específico.
    """
    query = db.query(LogAccion, User).join(User, LogAccion.usuario_id == User.uid, isouter=True)
    query = query.filter(LogAccion.usuario_id == usuario_id)
    results = query.order_by(LogAccion.fecha.desc()).limit(limit).all()

    return [
        {
            "id": log.id,
            "usuario_id": log.usuario_id,
            "usuario": user.nombre if user else f"User {log.usuario_id}",
            "tipo_evento": log.tipo_evento,
            "descripcion": log.descripcion,
            "link": log.link,  # Campo para hacer clickeable
            "fecha": log.fecha
        }
        for log, user in results
    ]


# ---------------------------
# Logs con datos del usuario
# ---------------------------
def obtener_logs_con_usuarios(db: Session, usuario_id: int = None, limit: int = 100):
    """
    Retorna logs con datos de usuario.
    Si se pasa usuario_id, retorna solo los logs de ese usuario.
    """
    query = db.query(LogAccion, User).join(User, LogAccion.usuario_id == User.uid, isouter=True)

    if usuario_id:
        query = query.filter(LogAccion.usuario_id == usuario_id)

    results = query.order_by(LogAccion.fecha.desc()).limit(limit).all()

    return [
        {
            "id": log.id,
            "usuario_id": log.usuario_id,
            "usuario": user.nombre if user else f"User {log.usuario_id}",
            "tipo_evento": log.tipo_evento,
            "descripcion": log.descripcion,
            "fecha": log.fecha
        }
        for log, user in results
    ]

# ---------------------------
# Bitácora de actividad por usuario (¡FUNCIÓN MODIFICADA!)
# ---------------------------
def obtener_bitacora_usuario(
    db: Session, 
    usuario_id: str, # El router envía un UID (str)
    fecha_inicio: Optional[date] = None, # <-- CAMBIO: Acepta fecha_inicio
    fecha_fin: Optional[date] = None      # <-- CAMBIO: Acepta fecha_fin
):
    """
    Retorna toda la bitácora de actividades de un usuario específico,
    filtrada opcionalmente por un rango de fechas.
    """
    # 1. Consulta base (igual que antes)
    query = db.query(LogAccion, User).join(User, LogAccion.usuario_id == User.uid, isouter=True)
    query = query.filter(LogAccion.usuario_id == usuario_id)

    # --- CAMBIO: APLICAR FILTROS DE FECHA ---
    if fecha_inicio:
        # Asumiendo que LogAccion.fecha es una columna de tipo DateTime o Timestamp
        query = query.filter(LogAccion.fecha >= fecha_inicio)
    
    if fecha_fin:
        # Para incluir el día completo de 'fecha_fin', filtramos hasta el inicio del *siguiente* día
        # ej. Si fecha_fin es 2025-10-31, filtramos por < 2025-11-01
        fecha_fin_ajustada = fecha_fin + timedelta(days=1)
        query = query.filter(LogAccion.fecha < fecha_fin_ajustada)
    # --- FIN DEL CAMBIO ---

    # 3. Ejecutar consulta (eliminamos el limit=100 para traer todo el rango)
    results = query.order_by(LogAccion.fecha.desc()).all()

    return [
        {
            "id": log.id,
            "usuario_id": log.usuario_id,
            "usuario": user.nombre if user else f"User {log.usuario_id}",
            "tipo_evento": log.tipo_evento,
            "descripcion": log.descripcion,
            "fecha": log.fecha
        }
        for log, user in results
    ]


def obtener_usuarios_por_rol(db: Session, rol_nombre: str) -> List[User]:
    """Obtener usuarios por nombre de rol."""
    return db.query(User).join(User.roles).filter(User.roles.any(name=rol_nombre)).all()


def crear_notificacion(db: Session, usuario_id: str, tipo_evento: str, descripcion: str, link: str = None):
    """Crear una notificación individual."""
    nuevo_log = LogAccion(
        usuario_id=usuario_id,
        tipo_evento=tipo_evento,
        descripcion=descripcion,
        link=link
    )
    db.add(nuevo_log)
    db.commit()
    db.refresh(nuevo_log)
    return nuevo_log


def notificar_proyecto_creado(db: Session, proyecto_id: int, proyecto_nombre: str, cliente_nombre: str, creador_id: str):
    """Notificar cuando se crea un proyecto."""
    if creador_id:
        link = f"/r/superadmin/projects/edit.html?id={proyecto_id}"
        crear_notificacion(
            db=db,
            usuario_id=creador_id,
            tipo_evento="proyecto_creado",
            descripcion=f"📁 Proyecto '{proyecto_nombre}' creado para cliente {cliente_nombre}",
            link=link
        )


def notificar_tarea_creada(db: Session, tarea_titulo: str, proyecto_nombre: str, asignado_nombre: str, creador_id: str):
    """Notificar cuando se crea una tarea."""
    if creador_id:
        crear_notificacion(
            db=db,
            usuario_id=creador_id,
            tipo_evento="tarea_creada",
            descripcion=f"✅ Tarea '{tarea_titulo}' creada en proyecto '{proyecto_nombre}' - Asignado a: {asignado_nombre}"
        )


def notificar_plan_estudio_creado(db: Session, plan_id: int, plan_nombre: str, proyecto_nombre: str, creador_id: str):
    """Notificar cuando se crea un plan de estudio."""
    if creador_id:
        link = f"/r/superadmin/study-plans/edit.html?id={plan_id}"
        crear_notificacion(
            db=db,
            usuario_id=creador_id,
            tipo_evento="plan_estudio_creado",
            descripcion=f"📚 Plan de estudio '{plan_nombre}' creado en proyecto '{proyecto_nombre}'",
            link=link
        )

