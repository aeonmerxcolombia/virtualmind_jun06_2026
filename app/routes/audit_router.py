# app/routes/audit_router.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.database.db import SessionLocal
from app.models.user import User
from app.models.audit_log import AuditLog
from app.auth.jwt_handler import verify_token
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import json

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AuditLogCreate(BaseModel):
    ip: str
    ciudad: Optional[str] = None
    pais: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None


class SessionClose(BaseModel):
    duracion_segundos: Optional[int] = None
    paginas_visitadas: Optional[List[str]] = None


@router.post("/registrar-entrada")
def registrar_entrada(
    request: Request,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    user_uid = token_data.get("user_id")
    ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    
    ciudad = request.headers.get("X-City", None)
    pais = request.headers.get("X-Country", None)
    lat = request.headers.get("X-Latitude", None)
    lon = request.headers.get("X-Longitude", None)
    
    ciudad = ciudad if ciudad else None
    pais = pais if pais else None
    latitud = float(lat) if lat else None
    longitud = float(lon) if lon else None
    
    audit = AuditLog(
        user_uid=user_uid,
        ip=ip,
        ciudad=ciudad,
        pais=pais,
        latitud=latitud,
        longitud=longitud,
        fecha_entrada=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    
    return {"id": audit.id, "msg": "Entrada registrada"}


@router.post("/registrar-salida/{session_id}")
def registrar_salida(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    session = db.query(AuditLog).filter(AuditLog.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    session.fecha_salida = datetime.utcnow()
    
    if session.fecha_entrada:
        duracion = (session.fecha_salida - session.fecha_entrada).total_seconds()
        session.duracion_segundos = int(duracion)
    
    paginas_raw = request.headers.get("X-Pages-Visited", "[]")
    try:
        paginas_list = json.loads(paginas_raw)
        session.paginas_visitadas = json.dumps(paginas_list)
    except:
        session.paginas_visitadas = "[]"
    
    db.commit()
    
    return {"msg": "Sesión cerrada", "duracion_segundos": session.duracion_segundos}


@router.get("/")
def listar_auditoria(
    skip: int = 0,
    limit: int = 50,
    user_uid: Optional[str] = None,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    query = db.query(AuditLog, User.nombre, User.email).join(
        User, AuditLog.user_uid == User.uid
    )
    
    if user_uid:
        query = query.filter(AuditLog.user_uid == user_uid)
    
    total = query.count()
    results = query.order_by(AuditLog.fecha_entrada.desc()).offset(skip).limit(limit).all()
    
    data = []
    for audit, nombre, email in results:
        paginas = []
        if audit.paginas_visitadas:
            try:
                paginas = json.loads(audit.paginas_visitadas)
            except:
                paginas = []
        
        data.append({
            "id": audit.id,
            "user_uid": audit.user_uid,
            "user_nombre": nombre,
            "user_email": email,
            "ip": audit.ip,
            "ciudad": audit.ciudad,
            "pais": audit.pais,
            "latitud": audit.latitud,
            "longitud": audit.longitud,
            "fecha_entrada": audit.fecha_entrada.isoformat() if audit.fecha_entrada else None,
            "fecha_salida": audit.fecha_salida.isoformat() if audit.fecha_salida else None,
            "duracion_segundos": audit.duracion_segundos,
            "paginas_visitadas": paginas
        })
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": data
    }


@router.get("/usuarios")
def listar_usuarios_con_auditoria(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    query = text("""
        SELECT 
            u.uid,
            u.nombre,
            u.email,
            COUNT(a.id) as total_sesiones,
            COALESCE(SUM(a.duracion_segundos), 0) as tiempo_total_segundos,
            MIN(a.fecha_entrada) as primera_sesion,
            MAX(a.fecha_entrada) as ultima_sesion
        FROM usuarios u
        LEFT JOIN auditoria a ON u.uid = a.user_uid
        GROUP BY u.uid, u.nombre, u.email
        ORDER BY total_sesiones DESC
        LIMIT 100
    """)
    results = db.execute(query).fetchall()
    
    data = []
    for row in results:
        data.append({
            "uid": row[0],
            "nombre": row[1],
            "email": row[2],
            "total_sesiones": row[3],
            "tiempo_total_segundos": row[4],
            "tiempo_total_formato": format_duration(row[4]),
            "primera_sesion": row[5].isoformat() if row[5] else None,
            "ultima_sesion": row[6].isoformat() if row[6] else None
        })
    
    return data


@router.get("/estadisticas")
def estadisticas_auditoria(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    total_sesiones = db.query(func.count(AuditLog.id)).scalar()
    sesiones_activas = db.query(func.count(AuditLog.id)).filter(
        AuditLog.fecha_salida.is_(None)
    ).scalar()
    
    query = text("""
        SELECT COUNT(DISTINCT user_uid) as usuarios_activos
        FROM auditoria
        WHERE fecha_entrada >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)
    usuarios_activos_30 = db.execute(query).scalar()
    
    return {
        "total_sesiones": total_sesiones,
        "sesiones_activas": sesiones_activas,
        "usuarios_activos_30_dias": usuarios_activos_30
    }


@router.get("/mapa")
def datos_mapa(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    query = text("""
        SELECT ciudad, pais, latitud, longitud, COUNT(*) as cantidad
        FROM auditoria
        WHERE latitud IS NOT NULL AND longitud IS NOT NULL
        GROUP BY ciudad, pais, latitud, longitud
        ORDER BY cantidad DESC
        LIMIT 50
    """)
    results = db.execute(query).fetchall()
    
    data = []
    for row in results:
        data.append({
            "ciudad": row[0],
            "pais": row[1],
            "latitud": float(row[2]) if row[2] else None,
            "longitud": float(row[3]) if row[3] else None,
            "cantidad": row[4]
        })
    
    return data


def format_duration(seconds):
    if not seconds:
        return "0s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
