from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
from pydantic import BaseModel
import requests
import os
from app.database.db import get_db
from app.models.laboratorio_vr import LaboratorioVR, ModeloVR, ExperimentoVR, SesionVR
from app.auth.jwt_handler import verify_token

router = APIRouter(prefix="/laboratorios-vr", tags=["Laboratorios VR"])


# === SCHEMAS ===
class LaboratorioVRBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    categoria: Optional[str] = "general"
    modelo_3d: Optional[str] = None
    escenario: Optional[str] = "laboratorio"
    contenido: Optional[dict] = None
    estado: Optional[str] = "activo"


class LaboratorioVRCreate(LaboratorioVRBase):
    pass


class LaboratorioVRUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    modelo_3d: Optional[str] = None
    escenario: Optional[str] = None
    contenido: Optional[dict] = None
    estado: Optional[str] = None


class ModeloVRBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    tipo: Optional[str] = "primitive"
    archivo: Optional[str] = None
    geometry_data: Optional[dict] = None
    material_data: Optional[dict] = None
    posicion: Optional[str] = "0 1.5 -2"
    rotacion: Optional[str] = "0 0 0"
    escala: Optional[str] = "1 1 1"
    animacion: Optional[dict] = None


class ModeloVRCreate(ModeloVRBase):
    pass


class ExperimentoVRBase(BaseModel):
    laboratorio_id: int
    nombre: str
    descripcion: Optional[str] = None
    pasos: list
    modelos_requeridos: Optional[list] = None
    evaluacion: Optional[dict] = None
    duracion_estimada: Optional[int] = 30
    dificultad: Optional[str] = "basico"
    estado: Optional[str] = "activo"


class ExperimentoVRCreate(ExperimentoVRBase):
    pass


class SesionVRCreate(BaseModel):
    usuario_id: int
    laboratorio_id: Optional[int] = None
    experimento_id: Optional[int] = None
    modelo_id: Optional[int] = None


class SesionVRUpdate(BaseModel):
    respuesta: Optional[str] = None
    duracion: Optional[int] = None
    resultado: Optional[dict] = None
    completado: Optional[bool] = None


# === LABORATORIOS ===


@router.get("/")
async def listar_laboratorios(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    categoria: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    query = db.query(LaboratorioVR)

    if categoria:
        query = query.filter(LaboratorioVR.categoria == categoria)

    total = query.count()
    laboratorios = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": l.id,
                "nombre": l.nombre,
                "descripcion": l.descripcion,
                "categoria": l.categoria,
                "modelo_3d": l.modelo_3d,
                "escenario": l.escenario,
                "estado": l.estado,
                "fecha_creacion": l.fecha_creacion.isoformat()
                if l.fecha_creacion
                else None,
            }
            for l in laboratorios
        ],
    }


@router.get("/{laboratorio_id}")
async def obtener_laboratorio(
    laboratorio_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    lab = db.query(LaboratorioVR).filter(LaboratorioVR.id == laboratorio_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado")

    return {
        "id": lab.id,
        "nombre": lab.nombre,
        "descripcion": lab.descripcion,
        "categoria": lab.categoria,
        "modelo_3d": lab.modelo_3d,
        "escenario": lab.escenario,
        "contenido": lab.contenido,
        "estado": lab.estado,
        "fecha_creacion": lab.fecha_creacion.isoformat()
        if lab.fecha_creacion
        else None,
    }


@router.post("/")
async def crear_laboratorio(
    laboratorio: LaboratorioVRCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    db_lab = LaboratorioVR(
        nombre=laboratorio.nombre,
        descripcion=laboratorio.descripcion,
        categoria=laboratorio.categoria,
        modelo_3d=laboratorio.modelo_3d,
        escenario=laboratorio.escenario,
        contenido=laboratorio.contenido,
        estado=laboratorio.estado,
        usuario_creacion=current_user.get("id"),
    )
    db.add(db_lab)
    db.commit()
    db.refresh(db_lab)

    return {
        "id": db_lab.id,
        "nombre": db_lab.nombre,
        "mensaje": "Laboratorio creado exitosamente",
    }


@router.put("/{laboratorio_id}")
async def actualizar_laboratorio(
    laboratorio_id: int,
    laboratorio: LaboratorioVRUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    db_lab = db.query(LaboratorioVR).filter(LaboratorioVR.id == laboratorio_id).first()
    if not db_lab:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado")

    for key, value in laboratorio.dict(exclude_unset=True).items():
        setattr(db_lab, key, value)

    db.commit()
    db.refresh(db_lab)

    return {
        "id": db_lab.id,
        "nombre": db_lab.nombre,
        "mensaje": "Laboratorio actualizado",
    }


@router.delete("/{laboratorio_id}")
async def eliminar_laboratorio(
    laboratorio_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    db_lab = db.query(LaboratorioVR).filter(LaboratorioVR.id == laboratorio_id).first()
    if not db_lab:
        raise HTTPException(status_code=404, detail="Laboratorio no encontrado")

    db.delete(db_lab)
    db.commit()

    return {"mensaje": "Laboratorio eliminado"}


# === MODELOS 3D ===


@router.get("/modelos/")
async def listar_modelos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    categoria: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    query = db.query(ModeloVR)

    if categoria:
        query = query.filter(ModeloVR.categoria == categoria)

    total = query.count()
    modelos = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": m.id,
                "nombre": m.nombre,
                "descripcion": m.descripcion,
                "categoria": m.categoria,
                "tipo": m.tipo,
                "archivo": m.archivo,
                "geometry_data": m.geometry_data,
                "material_data": m.material_data,
                "posicion": m.posicion,
                "rotacion": m.rotacion,
                "escala": m.escala,
                "animacion": m.animacion,
            }
            for m in modelos
        ],
    }


@router.post("/modelos/")
async def crear_modelo(
    modelo: ModeloVRCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    db_modelo = ModeloVR(
        nombre=modelo.nombre,
        descripcion=modelo.descripcion,
        categoria=modelo.categoria,
        tipo=modelo.tipo,
        archivo=modelo.archivo,
        geometry_data=modelo.geometry_data,
        material_data=modelo.material_data,
        posicion=modelo.posicion,
        rotacion=modelo.rotacion,
        escala=modelo.escala,
        animacion=modelo.animacion,
        usuario_creacion=current_user.get("id"),
    )
    db.add(db_modelo)
    db.commit()
    db.refresh(db_modelo)

    return {"id": db_modelo.id, "nombre": db_modelo.nombre, "mensaje": "Modelo creado"}


# === EXPERIMENTOS ===


@router.get("/experimentos/")
async def listar_experimentos(
    laboratorio_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    query = db.query(ExperimentoVR)
    if laboratorio_id:
        query = query.filter(ExperimentoVR.laboratorio_id == laboratorio_id)

    experimentos = query.all()

    return {
        "items": [
            {
                "id": e.id,
                "laboratorio_id": e.laboratorio_id,
                "nombre": e.nombre,
                "descripcion": e.descripcion,
                "pasos": e.pasos,
                "duracion_estimada": e.duracion_estimada,
                "dificultad": e.dificultad,
            }
            for e in experimentos
        ]
    }


@router.post("/experimentos/")
async def crear_experimento(
    experimento: ExperimentoVRCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    db_exp = ExperimentoVR(
        laboratorio_id=experimento.laboratorio_id,
        nombre=experimento.nombre,
        descripcion=experimento.descripcion,
        pasos=experimento.pasos,
        modelos_requeridos=experimento.modelos_requeridos,
        evaluacion=experimento.evaluacion,
        duracion_estimada=experimento.duracion_estimada,
        dificultad=experimento.dificultad,
        estado=experimento.estado,
    )
    db.add(db_exp)
    db.commit()
    db.refresh(db_exp)

    return {"id": db_exp.id, "nombre": db_exp.nombre, "mensaje": "Experimento creado"}


# === SESIONES ===


@router.get("/sesiones/")
async def listar_sesiones(
    usuario_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    query = db.query(SesionVR)
    if usuario_id:
        query = query.filter(SesionVR.usuario_id == usuario_id)

    sesiones = query.order_by(SesionVR.fecha_inicio.desc()).limit(50).all()

    return {
        "items": [
            {
                "id": s.id,
                "usuario_id": s.usuario_id,
                "laboratorio_id": s.laboratorio_id,
                "experimento_id": s.experimento_id,
                "duracion": s.duracion,
                "completado": s.completado,
                "fecha_inicio": s.fecha_inicio.isoformat() if s.fecha_inicio else None,
            }
            for s in sesiones
        ]
    }


@router.post("/sesiones/")
async def crear_sesion(
    sesion: SesionVRCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    db_sesion = SesionVR(
        usuario_id=sesion.usuario_id or current_user.get("id"),
        laboratorio_id=sesion.laboratorio_id,
        experimento_id=sesion.experimento_id,
        modelo_id=sesion.modelo_id,
        fecha_inicio=func.now(),
    )
    db.add(db_sesion)
    db.commit()
    db.refresh(db_sesion)

    return {"id": db_sesion.id, "mensaje": "Sesión iniciada"}


@router.put("/sesiones/{sesion_id}")
async def actualizar_sesion(
    sesion_id: int,
    sesion: SesionVRUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    db_sesion = db.query(SesionVR).filter(SesionVR.id == sesion_id).first()
    if not db_sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    for key, value in sesion.dict(exclude_unset=True).items():
        setattr(db_sesion, key, value)

    db.commit()

    return {"mensaje": "Sesión actualizada"}


# === GUÍA IA PARA VR ===


@router.post("/guia/")
async def obtener_guia_vr(
    laboratorio_id: int = 0,
    pregunta: str = "",
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """
    Obtener guía de IA para un laboratorio VR específico.
    Usa Gemini con contexto del laboratorio y documentación de VirtualMind.
    También puede crear nuevos laboratorios si el usuario lo pide.
    laboratorio_id=0 es para preguntas generales.
    """
    if not pregunta:
        raise HTTPException(status_code=422, detail="Se requiere una pregunta")

    # Verificar si es una petición de crear laboratorio
    crear_keywords = [
        "créalo",
        "crear laboratorio",
        "nuevo laboratorio",
        "créate",
        "genéralo",
        "crea un",
    ]
    crear_peticion = any(kw in pregunta.lower() for kw in crear_keywords)

    # Si es crear, primero pedir a Gemini que genere el contenido del laboratorio
    if crear_peticion:
        lab = None
        if laboratorio_id > 0:
            lab = (
                db.query(LaboratorioVR)
                .filter(LaboratorioVR.id == laboratorio_id)
                .first()
            )

        prompt_crear = f"""Eres un creador de laboratorios de Realidad Virtual para VirtualMind.

Basándote en este tema del usuario: {pregunta}

Genera UN SOLO laboratorio VR en formato JSON con esta estructura EXACTA:
{{
  "nombre": "Laboratorio: [nombre corto]",
  "descripcion": "[descripción de 1-2 oraciones]",
  "categoria": "formacion",
  "modelo_3d": "[uno de: panel, proyectos, usuarios, ia, modulos, seguridad, articulate, api, notificaciones, database]",
  "escenario": "laboratorio",
  "contenido": {{
    "objetivos": ["obj1", "obj2", "obj3"],
    "temas": ["tema1", "tema2"],
    "permisos": "[permiso requerido]"
  }}
}}

Responde SOLO con el JSON, sin texto adicional."""

        from app.services.ai.gemini_pool import get_gemini_key

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={get_gemini_key()}"
        body = {"contents": [{"parts": [{"text": prompt_crear}]}]}

        try:
            response = requests.post(
                url, headers={"Content-Type": "application/json"}, json=body, timeout=60
            )
            data = response.json()
            texto_respuesta = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "{}")
            )

            # Parsear el JSON
            import json
            import re

            # Extraer JSON de la respuesta
            json_match = re.search(r"\{[^{}]*\}", texto_respuesta, re.DOTALL)
            if json_match:
                lab_data = json.loads(json_match.group())

                # Crear el laboratorio en BD
                nuevo_lab = LaboratorioVR(
                    nombre=lab_data.get("nombre", "Nuevo Laboratorio"),
                    descripcion=lab_data.get("descripcion", ""),
                    categoria=lab_data.get("categoria", "formacion"),
                    modelo_3d=lab_data.get("modelo_3d", "panel"),
                    escenario=lab_data.get("escenario", "laboratorio"),
                    contenido=lab_data.get("contenido"),
                    estado="activo",
                    usuario_creacion=current_user.get("id"),
                )
                db.add(nuevo_lab)
                db.commit()
                db.refresh(nuevo_lab)

                return {
                    "laboratorio": lab.nombre if lab else "Sistema",
                    "pregunta": pregunta,
                    "respuesta": f"✅ ¡Laboratorio creado exitosamente!\n\n📛 Nombre: {nuevo_lab.nombre}\n📝 Descripción: {nuevo_lab.descripcion}\n\nAhora puedes verlo en la lista de Laboratorios y probarlo.",
                    "nuevo_laboratorio": {
                        "id": nuevo_lab.id,
                        "nombre": nuevo_lab.nombre,
                    },
                }
        except Exception as e:
            return {
                "laboratorio": "Sistema",
                "pregunta": pregunta,
                "respuesta": f"❌ Error al crear: {str(e)}. Intenta de nuevo.",
            }

    # Obtener laboratorio (opcional para preguntas generales)
    lab = None
    if laboratorio_id > 0:
        lab = db.query(LaboratorioVR).filter(LaboratorioVR.id == laboratorio_id).first()

    if lab:
        contexts = {
            "guiado": """Eres un guía virtual en un tour por el panel de VirtualMind.
Explicas las herramientas disponibles y cómo navegar los menús.""",
            "formacion": """Eres un instructor virtual de VirtualMind.
Explicas cómo usar las herramientas de la plataforma paso a paso.""",
            "default": """Eres un asistente virtual de Realidad Virtual.
Ayudas al usuario a comprender y navegar el contenido 3D.""",
        }
        context = contexts.get(lab.categoria, contexts["default"])
        prompt = f"""Eres un guía de Realidad Virtual para VirtualMind.

CONTEXTO DEL LABORATORIO:
- Nombre: {lab.nombre}
- Descripción: {lab.descripcion or "Sin descripción"}
- Categoría: {lab.categoria}

{context}

PREGUNTA DEL USUARIO: {pregunta}

Responde de manera clara y concisa. Si hay pasos a seguir, enuméralos.
Si el usuario necesita hacer algo en el visor VR, descríbelo."""
        lab_name = lab.nombre
    else:
        prompt = f"""Eres un guía de aprendizaje virtual para VirtualMind Learning World.

Eres un asistente experto en educación y tecnología. Tu objetivo es:
- Responder preguntas sobre cualquier tema de aprendizaje
- Explicar conceptos de forma clara y educativa
- Sugerir recursos y rutas de aprendizaje
- Mantener un tono amigable y motivador

PREGUNTA DEL USUARIO: {pregunta}

Responde de manera clara, concisa y educativa. Si el usuario muestra interés en un tema en particular, ofrécete a crear un laboratorio de aprendizaje virtual sobre ese tema."""
        lab_name = "Learning World"

    # Llamar a Gemini
    from app.services.ai.gemini_pool import get_gemini_key

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={get_gemini_key()}"
    body = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(
            url, headers={"Content-Type": "application/json"}, json=body, timeout=60
        )
        data = response.json()
        respuesta = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "Sin respuesta")
        )
        return {"laboratorio": lab_name, "pregunta": pregunta, "respuesta": respuesta}
    except Exception as e:
        return {
            "laboratorio": lab_name,
            "pregunta": pregunta,
            "respuesta": f"⚠️ Error de IA: {str(e)}. Prueba usando el visor VR con los controles WASD.",
        }


# === ESTADÍSTICAS ===


@router.get("/stats/")
async def obtener_stats(
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token)
):
    total_labs = db.query(LaboratorioVR).count()
    total_modelos = db.query(ModeloVR).count()
    total_exps = db.query(ExperimentoVR).count()
    total_sesiones = db.query(SesionVR).count()

    return {
        "laboratorios": total_labs,
        "modelos": total_modelos,
        "experimentos": total_exps,
        "sesiones": total_sesiones,
    }
