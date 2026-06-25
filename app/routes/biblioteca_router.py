from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os, json, requests, shutil
from datetime import datetime

from app.database.db import SessionLocal
from app.auth.jwt_handler import verify_token
from app.models.biblioteca import (
    DocumentoBiblioteca,
    AccesoBiblioteca,
    SolicitudAccesoBiblioteca,
)
from app.schemas.biblioteca_schema import DocumentoBibliotecaOut
from app.models.documento_office import (
    DocumentoOficina,
    DocumentoVersion,
    DocumentoRevision,
)
from app.models.project import Project
from app.services.log_service import crear_notificacion
from app.services.email_service import send_email, get_user_email

router = APIRouter(prefix="/biblioteca", tags=["Biblioteca de Documentos"])

BIBLIOTECA_DIR = "/home/ubuntu/backend/documentos/biblioteca"
os.makedirs(BIBLIOTECA_DIR, exist_ok=True)

from app.services.ai.gemini_pool import get_gemini_key

GEMINI_MODEL = "gemini-2.5-flash"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generar_nota_bibliografica(
    nombre: str, autor: str, proyecto: str, tipo: str, year: int
) -> str:

    prompt = f"""Genera una nota bibliográfica en formato APA 7ª edición para el siguiente documento:

Título: {nombre}
Autor: {autor}
Proyecto: {proyecto}
Tipo: {tipo}
Año: {year}

Responde SOLO con la cita bibliográfica en formato APA, sin explicaciones adicionales."""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={get_gemini_key()}"
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=body, timeout=30)
        data = resp.json()
        return (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )
    except Exception as e:
        return f"{autor} ({year}). {nombre}. {proyecto}."


# ---- LISTAR BIBLIOTECA (con filtro de permisos) ----
@router.get("/", response_model=List[DocumentoBibliotecaOut])
def listar_biblioteca(
    q: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    user_id = token_data.get("user_id", "")
    roles = token_data.get("roles", [])

    query = db.query(DocumentoBiblioteca)

    # Superadmin ve todo; otros ven solo documentos con acceso
    if "superadmin" not in roles:
        doc_ids_con_acceso = (
            db.query(AccesoBiblioteca.documento_id)
            .filter(
                (AccesoBiblioteca.usuario_id == user_id)
                | (AccesoBiblioteca.rol.in_(roles))
            )
            .distinct()
            .subquery()
        )
        query = query.filter(DocumentoBiblioteca.id.in_(doc_ids_con_acceso))

    if q:
        f = f"%{q}%"
        query = query.filter(
            DocumentoBiblioteca.nombre.ilike(f)
            | DocumentoBiblioteca.descripcion.ilike(f)
            | DocumentoBiblioteca.etiquetas.ilike(f)
            | DocumentoBiblioteca.usuario_nombre.ilike(f)
            | DocumentoBiblioteca.proyecto_nombre.ilike(f)
        )
    if tipo:
        query = query.filter(DocumentoBiblioteca.tipo == tipo)
    if project_id:
        query = query.filter(DocumentoBiblioteca.project_id == project_id)

    return query.order_by(DocumentoBiblioteca.fecha_ingreso.desc()).all()


# ---- OBTENER DOCUMENTO ----
@router.get("/{doc_id}", response_model=DocumentoBibliotecaOut)
def obtener_documento(
    doc_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    doc = db.query(DocumentoBiblioteca).filter(DocumentoBiblioteca.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


# ---- AGREGAR DOCUMENTO DESDE REVISIÓN APROBADA ----
@router.post("/agregar", response_model=DocumentoBibliotecaOut)
async def agregar_a_biblioteca(
    documento_id: int = Form(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    doc_office = (
        db.query(DocumentoOficina).filter(DocumentoOficina.id == documento_id).first()
    )
    if not doc_office:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if doc_office.estado_version not in ("aprobada", "cerrada"):
        raise HTTPException(
            status_code=400,
            detail="El documento debe estar en estado 'aprobada' o 'cerrada' para agregarse a la biblioteca",
        )

    ya_existe = (
        db.query(DocumentoBiblioteca)
        .filter(
            DocumentoBiblioteca.documento_id == documento_id,
            DocumentoBiblioteca.version == doc_office.version_actual,
        )
        .first()
    )
    if ya_existe:
        raise HTTPException(
            status_code=400,
            detail="Esta versión del documento ya está en la biblioteca",
        )

    project = db.query(Project).filter(Project.id == doc_office.project_id).first()
    proyecto_nombre = project.name if project else "Sin proyecto"

    from app.models.user import User

    user = db.query(User).filter(User.uid == doc_office.usuario_id).first()
    usuario_nombre = user.nombre if user else doc_office.usuario_id

    src = doc_office.ruta
    filename = f"bib_{doc_office.id}_v{doc_office.version_actual}_{os.path.basename(doc_office.filename)}"
    dst = os.path.join(BIBLIOTECA_DIR, filename)

    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy2(src, dst)

    year = datetime.now().year
    nota = generar_nota_bibliografica(
        nombre=doc_office.nombre,
        autor=usuario_nombre,
        proyecto=proyecto_nombre,
        tipo=doc_office.tipo,
        year=year,
    )

    doc_bib = DocumentoBiblioteca(
        documento_id=doc_office.id,
        project_id=doc_office.project_id,
        nombre=doc_office.nombre,
        tipo=doc_office.tipo,
        version=doc_office.version_actual or "1.0",
        filename=filename,
        ruta_archivo=dst,
        usuario_id=doc_office.usuario_id,
        usuario_nombre=usuario_nombre,
        proyecto_nombre=proyecto_nombre,
        descripcion="",
        etiquetas="",
        nota_bibliografica=nota,
    )
    db.add(doc_bib)
    db.flush()

    # Otorgar acceso al creador y a los roles del proyecto
    acceso_creador = AccesoBiblioteca(
        documento_id=doc_bib.id,
        usuario_id=doc_office.usuario_id,
        permiso="lectura",
    )
    db.add(acceso_creador)

    db.commit()
    db.refresh(doc_bib)

    # Notificar
    crear_notificacion(
        db=db,
        usuario_id=doc_office.usuario_id,
        tipo_evento="documento_biblioteca",
        descripcion=f"📚 Documento '{doc_office.nombre}' agregado a la biblioteca",
    )

    return doc_bib


# ---- GENERAR / REGENERAR NOTA BIBLIOGRÁFICA ----
@router.post("/{doc_id}/generar-nota")
def generar_nota_endpoint(
    doc_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    doc = db.query(DocumentoBiblioteca).filter(DocumentoBiblioteca.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    nota = generar_nota_bibliografica(
        nombre=doc.nombre,
        autor=doc.usuario_nombre or doc.usuario_id,
        proyecto=doc.proyecto_nombre or "",
        tipo=doc.tipo,
        year=datetime.now().year,
    )
    doc.nota_bibliografica = nota
    db.commit()
    return {"nota_bibliografica": nota}


# ---- GESTIÓN DE PERMISOS ----
@router.get("/{doc_id}/permisos")
def listar_permisos(
    doc_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    permisos = (
        db.query(AccesoBiblioteca).filter(AccesoBiblioteca.documento_id == doc_id).all()
    )
    return permisos


@router.post("/{doc_id}/permisos")
def asignar_permiso(
    doc_id: int,
    usuario_id: Optional[str] = Form(None),
    rol: Optional[str] = Form(None),
    permiso: str = Form("lectura"),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    roles_user = token_data.get("roles", [])
    if not any(
        r in roles_user for r in ("superadmin", "admin", "coordinador", "cliente")
    ):
        raise HTTPException(
            status_code=403, detail="No tienes permiso para gestionar accesos"
        )

    acceso = AccesoBiblioteca(
        documento_id=doc_id,
        usuario_id=usuario_id,
        rol=rol,
        permiso=permiso,
    )
    db.add(acceso)
    db.commit()
    return {"ok": True}


@router.delete("/{doc_id}/permisos/{acceso_id}")
def eliminar_permiso(
    doc_id: int,
    acceso_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    roles_user = token_data.get("roles", [])
    if "superadmin" not in roles_user and "admin" not in roles_user:
        raise HTTPException(status_code=403)
    acceso = db.query(AccesoBiblioteca).filter(AccesoBiblioteca.id == acceso_id).first()
    if acceso:
        db.delete(acceso)
        db.commit()
    return {"ok": True}


# ---- SOLICITUDES DE ACCESO ----
@router.post("/{doc_id}/solicitar-acceso")
async def solicitar_acceso(
    doc_id: int,
    razon: str = Form(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    doc = db.query(DocumentoBiblioteca).filter(DocumentoBiblioteca.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    user_id = token_data.get("user_id")

    ya_existe = (
        db.query(SolicitudAccesoBiblioteca)
        .filter(
            SolicitudAccesoBiblioteca.documento_id == doc_id,
            SolicitudAccesoBiblioteca.solicitante_id == user_id,
            SolicitudAccesoBiblioteca.estado == "pendiente",
        )
        .first()
    )
    if ya_existe:
        raise HTTPException(
            status_code=400,
            detail="Ya tienes una solicitud pendiente para este documento",
        )

    from app.models.user import User

    user = db.query(User).filter(User.uid == user_id).first()
    nombre = user.nombre if user else user_id

    sol = SolicitudAccesoBiblioteca(
        documento_id=doc_id,
        solicitante_id=user_id,
        solicitante_nombre=nombre,
        razon=razon,
    )
    db.add(sol)
    db.commit()

    crear_notificacion(
        db=db,
        usuario_id=user_id,
        tipo_evento="solicitud_acceso",
        descripcion=f"🔑 Solicitaste acceso a '{doc.nombre}' en la biblioteca",
    )

    # Notificar por email a admins/superadmins
    from app.services.log_service import obtener_usuarios_por_rol
    from app.services.email_service import get_user_email

    admins = obtener_usuarios_por_rol(db, "superadmin")
    admin_emails = [u.email for u in admins if u.email]
    for email in admin_emails:
        await send_email(
            to=email,
            subject=f"🔑 Nueva solicitud de acceso: {doc.nombre}",
            body=f"El usuario {nombre} ({user_id}) ha solicitado acceso al documento '{doc.nombre}'.\n\n"
            f"Razón: {razon}\n\n"
            f"Ingresa al panel de Biblioteca > Solicitudes para gestionarla.",
        )

    return {
        "ok": True,
        "mensaje": "Solicitud enviada. Recibirás una respuesta cuando sea gestionada.",
    }


@router.get("/solicitudes/pendientes")
def listar_solicitudes_pendientes(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    roles_user = token_data.get("roles", [])
    if not any(
        r in roles_user for r in ("superadmin", "admin", "coordinador", "cliente")
    ):
        raise HTTPException(status_code=403)

    solicitudes = (
        db.query(SolicitudAccesoBiblioteca, DocumentoBiblioteca)
        .join(
            DocumentoBiblioteca,
            SolicitudAccesoBiblioteca.documento_id == DocumentoBiblioteca.id,
        )
        .filter(SolicitudAccesoBiblioteca.estado == "pendiente")
        .order_by(SolicitudAccesoBiblioteca.fecha_solicitud.desc())
        .all()
    )

    return [
        {
            "id": s.id,
            "documento_id": s.documento_id,
            "documento_nombre": d.nombre,
            "solicitante_id": s.solicitante_id,
            "solicitante_nombre": s.solicitante_nombre,
            "razon": s.razon,
            "estado": s.estado,
            "fecha_solicitud": str(s.fecha_solicitud),
        }
        for s, d in solicitudes
    ]


@router.put("/solicitudes/{solicitud_id}")
async def resolver_solicitud_acceso(
    solicitud_id: int,
    estado: str = Form(...),
    respuesta_admin: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    roles_user = token_data.get("roles", [])
    if not any(
        r in roles_user for r in ("superadmin", "admin", "coordinador", "cliente")
    ):
        raise HTTPException(status_code=403)

    sol = (
        db.query(SolicitudAccesoBiblioteca)
        .filter(SolicitudAccesoBiblioteca.id == solicitud_id)
        .first()
    )
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if estado not in ("aprobada", "rechazada"):
        raise HTTPException(
            status_code=400, detail="Estado debe ser 'aprobada' o 'rechazada'"
        )

    sol.estado = estado
    sol.respuesta_admin = respuesta_admin
    sol.fecha_resolucion = datetime.utcnow()
    sol.resuelto_por = token_data.get("user_id")

    if estado == "aprobada":
        acceso = AccesoBiblioteca(
            documento_id=sol.documento_id,
            usuario_id=sol.solicitante_id,
            permiso="lectura",
        )
        db.add(acceso)

    db.commit()

    doc = (
        db.query(DocumentoBiblioteca)
        .filter(DocumentoBiblioteca.id == sol.documento_id)
        .first()
    )
    if doc:
        emoji = "✅" if estado == "aprobada" else "❌"
        crear_notificacion(
            db=db,
            usuario_id=sol.solicitante_id,
            tipo_evento=f"acceso_{estado}",
            descripcion=f"{emoji} Tu solicitud de acceso a '{doc.nombre}' fue {estado}",
        )
        email = get_user_email(db, sol.solicitante_id)
        if email:
            await send_email(
                to=email,
                subject=f"{emoji} Acceso {estado}: {doc.nombre}",
                body=f"Tu solicitud de acceso al documento '{doc.nombre}' fue {estado}.\n"
                + (f"Comentario: {respuesta_admin}\n" if respuesta_admin else ""),
            )

    return {"ok": True, "estado": estado}


# ---- ELIMINAR ----
@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_de_biblioteca(
    doc_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    roles = token_data.get("roles", [])
    if "superadmin" not in roles:
        raise HTTPException(
            status_code=403, detail="Solo superadmin puede eliminar de la biblioteca"
        )

    doc = db.query(DocumentoBiblioteca).filter(DocumentoBiblioteca.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if os.path.exists(doc.ruta_archivo):
        try:
            os.remove(doc.ruta_archivo)
        except:
            pass

    db.delete(doc)
    db.commit()
    return None


# ---- DESCARGAR ----
@router.get("/archivo/{filename}")
async def descargar_archivo_biblioteca(filename: str):
    filepath = os.path.join(BIBLIOTECA_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    from fastapi.responses import FileResponse

    return FileResponse(filepath, filename=filename)
