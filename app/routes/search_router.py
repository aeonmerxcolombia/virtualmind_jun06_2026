from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from app.database.db import get_db
from app.models.project import Project
from app.models.user import User
from app.models.tarea import Tarea
from app.auth.jwt_handler import verify_token

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/")
def search_global(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query 'q' is required")

    like = f"%{query}%"
    user_roles = token_data.get("roles", [])
    user_id = token_data.get("sub")
    results = []

    # --- Projects ---
    from app.models.proyecto_participante import ProyectoParticipante
    projects_q = db.query(Project, User.nombre.label("client_name")).outerjoin(User, Project.client_id == User.uid).filter(
        or_(
            Project.name.ilike(like),
            Project.description.ilike(like),
            Project.codigo_referencia.ilike(like),
            User.nombre.ilike(like),
            User.email.ilike(like),
        )
    )
    if "superadmin" not in user_roles:
        pids = [p.project_id for p in db.query(ProyectoParticipante).filter(ProyectoParticipante.user_uid == user_id).all()]
        projects_q = projects_q.filter(Project.id.in_(pids))
    for (p, client_name) in projects_q.limit(limit).all():
        results.append({
            "type": "proyecto",
            "id": p.id,
            "title": p.name,
            "subtitle": client_name or "",
            "url": f"/r/{user_roles[0] if user_roles else 'superadmin'}/projects/read.html?id={p.id}",
            "icon": "📁"
        })

    # --- Users ---
    users = db.query(User).filter(
        or_(
            User.nombre.ilike(like),
            User.email.ilike(like),
        )
    ).limit(limit).all()

    for u in users:
        results.append({
            "type": "usuario",
            "id": u.uid,
            "title": u.nombre,
            "subtitle": u.email or "",
            "url": f"/r/{user_roles[0] if user_roles else 'superadmin'}/usuarios/index.html?uid={u.uid}",
            "icon": "👤"
        })

    # --- Tareas ---
    tareas = db.query(Tarea).filter(
        or_(
            Tarea.titulo.ilike(like),
            Tarea.descripcion.ilike(like),
        )
    )
    if "superadmin" not in user_roles:
        tareas = tareas.filter(Tarea.usuario_id == user_id)
    tareas = tareas.limit(limit).all()

    for t in tareas:
        results.append({
            "type": "tarea",
            "id": t.id,
            "title": t.titulo,
            "subtitle": f"Vence: {t.fecha_vencimiento.strftime('%d/%m/%Y') if t.fecha_vencimiento else 'Sin fecha'}",
            "url": f"/r/{user_roles[0] if user_roles else 'superadmin'}/tasks/editar_tarea.html?id={t.id}",
            "icon": "✅"
        })

    # --- Bibliographic documents (if biblioteca model exists) ---
    try:
        from app.models.biblioteca import DocumentoBiblioteca
        docs = db.query(DocumentoBiblioteca).filter(
            or_(
                DocumentoBiblioteca.titulo.ilike(like),
                DocumentoBiblioteca.autores.ilike(like),
                DocumentoBiblioteca.palabras_clave.ilike(like),
                DocumentoBiblioteca.resumen.ilike(like),
            )
        )
        if "superadmin" not in user_roles:
            from app.models.biblioteca import AccesoBiblioteca
            doc_ids = [a.documento_id for a in db.query(AccesoBiblioteca).filter(
                or_(
                    AccesoBiblioteca.usuario_id == user_id,
                    AccesoBiblioteca.rol.in_(user_roles)
                )
            ).all()]
            docs = docs.filter(DocumentoBiblioteca.id.in_(doc_ids))
        docs = docs.limit(limit).all()

        for d in docs:
            results.append({
                "type": "documento",
                "id": d.id,
                "title": d.titulo,
                "subtitle": d.autores or "",
                "url": f"/r/{user_roles[0] if user_roles else 'superadmin'}/biblioteca/index.html?id={d.id}",
                "icon": "📄"
            })
    except Exception:
        pass

    # --- RRHH (hojas de vida) ---
    try:
        from app.models.rrhh import HojaVida
        hvs = db.query(HojaVida).filter(
            or_(
                HojaVida.nombre_completo.ilike(like),
                HojaVida.email.ilike(like),
                HojaVida.profesion.ilike(like),
                HojaVida.habilidades.ilike(like),
            )
        ).limit(limit).all()

        for hv in hvs:
            results.append({
                "type": "rrhh",
                "id": hv.id,
                "title": hv.nombre_completo,
                "subtitle": hv.profesion or hv.email or "",
                "url": f"/r/{user_roles[0] if user_roles else 'superadmin'}/rrhh/index.html?id={hv.id}",
                "icon": "👔"
            })
    except Exception:
        pass

    return {
        "results": results,
        "total": len(results),
        "query": query
    }
