import os
import json
import requests
import traceback
import asyncio
import re
import uuid
from fastapi import APIRouter, HTTPException, Header
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

# =================================================================
# 🧠 VIRTUALMIND MASTER ENGINE - OMEGA EDITION (V7.0)
# =================================================================
# Arquitectura de Alta Fidelidad - Zero Guesswork System
# Desarrollado por: Rosa (Elite AI Architect)
# Usuario: William Andrés (AI & Cyber-Security Specialist)
# =================================================================

router = APIRouter(prefix="/articulate", tags=["virtualmind_omega_engine"])

# --- 1. MODELOS DE DATOS DE ALTA FIDELIDAD (The DNA of Virtualmind) ---


class BlockContent(BaseModel):
    html: Optional[str] = None
    pregunta: Optional[str] = None
    opciones: Optional[List[Dict[str, Any]]] = None
    explicacion: Optional[str] = None
    url_imagen: Optional[str] = None
    url_video: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "allow"


class BlockStyles(BaseModel):
    background: Optional[str] = "#ffffff"
    color: Optional[str] = "#0f172a"
    padding: Optional[str] = "40px"
    borderRadius: Optional[str] = "32px"
    boxShadow: Optional[str] = "0 20px 50px rgba(0,0,0,0.03)"
    fontFamily: Optional[str] = "Inter"


class BlockSchema(BaseModel):
    id: str = Field(default_factory=lambda: f"block_{uuid.uuid4().hex[:8]}")
    tipo: str  # 'contenido_libre', 'interactivo_quiz', 'bento_grid', 'linea_tiempo', 'escenario_interactivo', 'flashcards_grid', 'chat_simulador', 'simulador_terminal', 'comparacion_lado', 'radar_chart', 'ruleta'
    tema: str
    contenido: BlockContent
    estilos: Optional[BlockStyles] = Field(default_factory=BlockStyles)


class MasterCourseResponse(BaseModel):
    courseTitle: str
    description: str
    blocks: List[BlockSchema]  # Exactamente 10 bloques en el generador maestro


class RefineResponse(BaseModel):
    html: str
    tema: str
    cambios_realizados: List[str]


class StorytellingResponse(BaseModel):
    moduleName: str
    narrative_arc: str
    metaphor: str
    suggested_blocks: List[BlockSchema]


class HookResponse(BaseModel):
    hooks: List[Dict[str, str]]  # { "tipo": "shock", "texto": "..." }


class AuditResponse(BaseModel):
    score: int
    suggestions: List[str]
    details: str


class AIRequest(BaseModel):
    prompt: str = ""
    contexto_actual: Any = None
    config: Optional[Dict[str, Any]] = {}


# --- 2. EL CEREBRO: VIRTUALMIND NEURAL CORE V7 ---


class VirtualmindBrain:
    def __init__(self):
        self.model_name = "gemini-2.5-flash"
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def _get_master_system_prompt(self, module_name: str):
        return f"""
        [SISTEMA DE MISIÓN CRÍTICA: {module_name}]
        ERES: El Arquitecto Principal de Virtualmind 360.
        MISIÓN: Generar estructuras JSON PERFECTAS.
        ESTÉTICA: Premium, futurista, local-first.
        REGLAS DE ORO:
        - NUNCA devuelvas Markdown ni explicaciones fuera del JSON.
        - El campo 'html' debe usar Tailwind CSS inline o estilos limpios.
        - Los bloques deben ser variados y pedagógicamente coherentes.
        """

    async def infer_specialized(
        self, module: str, system_instruction: str, user_data: Any, schema_class: Any
    ):
        from app.services.ai.gemini_pool import get_gemini_key

        url = f"{self.endpoint}?key={get_gemini_key()}"
        schema_info = schema_class.schema()

        prompt_final = f"""
        INSTRUCCIÓN: {system_instruction}
        DATOS DE REFERENCIA: {json.dumps(user_data)}
        
        DEBES GENERAR UN JSON QUE CUMPLA ESTE ESQUEMA:
        {json.dumps(schema_info)}
        """

        payload = {
            "contents": [{"parts": [{"text": prompt_final}]}],
            "systemInstruction": {
                "parts": [{"text": self._get_master_system_prompt(module)}]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.5,
                "maxOutputTokens": 8192,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=240)
            response.raise_for_status()
            raw_text = (
                response.json()
                .get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            data = json.loads(raw_text)
            # Validación forzada con Pydantic
            validated = schema_class(**data)
            return validated.dict()

        except Exception as e:
            print(f"ERROR OMEGA V7: {str(e)}")
            return {
                "error": "Fallo en la Sincronización Neural",
                "details": str(e),
                "is_error_object": True,
            }


brain = VirtualmindBrain()

# =================================================================
# 🚀 ENDPOINTS DE ALTA ESPECIALIZACIÓN (The Million Dollar API)
# =================================================================


@router.post("/ai/generate-component")
async def generate_component(request: AIRequest):
    """Endpoint genérico para auditoría y mejoras masivas (soporta Arrays y Objetos dinámicos)."""
    url = brain.endpoint + f"?key={brain.api_key}"
    system_instruction = "Eres el Arquitecto Experto de Virtualmind 360. Devuelve SOLO JSON VÁLIDO. Sin markdown, sin explicaciones. Si te piden un array de bloques, devuelve un array [{}]. Si te piden un bloque, devuelve un objeto {}."
    prompt_final = f"INSTRUCCIÓN:\n{request.prompt}\n\nCONTEXTO:\n{json.dumps(request.contexto_actual) if request.contexto_actual else ''}"

    payload = {
        "contents": [{"parts": [{"text": prompt_final}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3,
            "maxOutputTokens": 8192,
        },
    }
    try:
        response = requests.post(url, json=payload, timeout=240)
        response.raise_for_status()
        raw_text = (
            response.json()
            .get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        data = json.loads(raw_text)
        return data
    except Exception as e:
        print(f"ERROR GENERATE COMPONENT: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/generate/master-course")
async def generate_master_course(request: AIRequest):
    """Generador Maestro: Crea 10 bloques de nivel experto."""
    instruction = "Crea un curso completo de 10 bloques. Varía los tipos (quiz, bento, texto, imagen). Asegura una progresión pedagógica perfecta."
    return await brain.infer_specialized(
        "Master Course Architect", instruction, request.prompt, MasterCourseResponse
    )


@router.post("/ai/copy/refine-expert")
async def copy_refine(request: AIRequest):
    """Refinamiento de texto con estructura exacta."""
    instruction = "Refina los textos de este contenido para que el tono sea experto, premium y sofisticado. REGLA CRÍTICA: DEBES MANTENER ABSOLUTAMENTE INTACTA TODA la estructura de etiquetas HTML y atributos 'style' (estilos inline). SOLO modifica el texto legible."
    return await brain.infer_specialized(
        "Expert Refiner", instruction, request.contexto_actual, RefineResponse
    )


@router.post("/ai/game/story-arc-designer")
async def game_story(request: AIRequest):
    """Diseña la narrativa y sugiere bloques coherentes."""
    instruction = "Diseña un arco narrativo épico. Sugiere 3 bloques iniciales que sigan esa narrativa."
    return await brain.infer_specialized(
        "Story Arc Master", instruction, request.prompt, StorytellingResponse
    )


@router.post("/ai/copy/hook-generator")
async def copy_hooks(request: AIRequest):
    """Generador de Hooks psicológicos."""
    instruction = "Modifica los títulos o textos principales para convertirlos en 3 ganchos de atención potentes. REGLA CRÍTICA: DEBES MANTENER ABSOLUTAMENTE INTACTA TODA la estructura de etiquetas HTML y atributos 'style'. SOLO modifica el texto."
    return await brain.infer_specialized(
        "Hook Engine", instruction, request.contexto_actual, HookResponse
    )


@router.post("/ai/interact/auto-quiz")
async def interact_quiz(request: AIRequest):
    """Generador de Quices con validación de opciones."""
    instruction = "Crea un quiz de alta fidelidad con 4 opciones claras y una explicación técnica."
    return await brain.infer_specialized(
        "Quiz Generator", instruction, request.contexto_actual, BlockSchema
    )


@router.post("/ai/ui/bento-grid-architect")
async def ui_bento(request: AIRequest):
    """Arquitectura de Bento Grid Premium."""
    instruction = "Diseña una rejilla Bento con 4 celdas. Inyecta contenido relevante en cada una usando HTML elegante."
    return await brain.infer_specialized(
        "Bento Architect", instruction, request.contexto_actual, BlockSchema
    )


@router.post("/ai/copy/feynman-logic")
async def copy_feynman(request: AIRequest):
    """Técnica de Feynman para simplificar conceptos complejos."""
    instruction = "Aplica la técnica de Feynman al texto: simplifícalo usando analogías claras para un niño de 12 años sin perder el rigor técnico. REGLA CRÍTICA: DEBES MANTENER ABSOLUTAMENTE INTACTA TODA la estructura de etiquetas HTML y atributos 'style'. SOLO modifica el texto legible."
    return await brain.infer_specialized(
        "Feynman Simplifier", instruction, request.contexto_actual, RefineResponse
    )


@router.post("/ai/game/interactive-challenges")
async def interactive_challenges(request: AIRequest):
    """Generador de Retos Interactivos (Misiones)."""
    instruction = "Convierte este contenido teórico en un reto práctico o misión. Plantea una situación, opciones de decisión y consecuencias."
    return await brain.infer_specialized(
        "Mission Architect", instruction, request.contexto_actual, BlockSchema
    )


@router.post("/ai/audit/pedagogic-quality")
async def audit_pedagogic(request: AIRequest):
    """Auditoría de calidad pedagógica de un bloque o curso."""
    instruction = "Audita la calidad pedagógica de este contenido. Asigna un score de 0 a 100, da 3 sugerencias de mejora puntuales y un análisis detallado."
    return await brain.infer_specialized(
        "PhD Auditor", instruction, request.contexto_actual, AuditResponse
    )


# --- FIN DEL MOTOR OMEGA V7 ---
