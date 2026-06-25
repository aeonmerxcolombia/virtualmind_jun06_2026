# app/routes/whisper_router.py

from fastapi import APIRouter, UploadFile, File, HTTPException
import whisper
import tempfile
import os
import asyncio

router = APIRouter(prefix="/whisper", tags=["Audio IA / Whisper"])

# 1. Carga global del modelo. Se ejecuta solo una vez al iniciar FastAPI.
print("[IA] Cargando modelo Whisper en memoria...")
# Usamos 'base' por su excelente equilibrio entre velocidad y precisión en entornos de producción local
modelo_whisper = whisper.load_model("base")
print("[IA] Modelo Whisper listo para inferencia.")

@router.post("/transcribir")
async def transcribir_audio(audio: UploadFile = File(...)):
    """
    Recibe un archivo de audio (nota de voz) desde el frontend de VirtualMind,
    aplica contexto técnico para evitar alucinaciones y devuelve el texto transcrito.
    """
    extensiones_validas = [".mp3", ".wav", ".m4a", ".ogg", ".mp4", ".webm"]
    ext = os.path.splitext(audio.filename)[1].lower()

    # Validar extensión del archivo
    if ext not in extensiones_validas:
        raise HTTPException(
            status_code=400, 
            detail=f"Formato no soportado. Usa un formato válido: {', '.join(extensiones_validas)}"
        )

    # Leer el archivo en memoria (Límite higiénico de seguridad para proteger la RAM del catedraserver)
    contenido = await audio.read()
    if len(contenido) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El archivo de audio supera el límite de 25MB.")

    tmp_path = None
    try:
        # 2. Guardar el audio temporalmente en el almacenamiento del servidor
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(contenido)
            tmp_path = tmp.name

        # PROMPT DE CONTEXTO: Entrena el vocabulario de Whisper para el ecosistema de VirtualMind
        contexto_tecnico = (
            "Plan de formación, curso, diseño instruccional, IA Generativa, "
            "inteligencia artificial, módulos, objetivos específicos, trigonometría, "
            "competencias, aprendizaje, VirtualMind, software, ingeniería."
        )

        # 3. Ejecutar la inferencia en un Hilo Secundario para NO bloquear el loop de FastAPI
        # Añadimos temperature=0.0 para obligar al modelo a ser preciso y evitar que invente palabras con el ruido
        resultado = await asyncio.to_thread(
            modelo_whisper.transcribe,
            tmp_path,
            language="es",
            temperature=0.0,
            initial_prompt=contexto_tecnico
        )

        texto_final = resultado["text"].strip()

        # Opcional: Si el modelo devuelve balbuceos o el audio fue puro ruido de fondo
        if texto_final.lower() in ["por ver.", "gracias.", "subtítulos por amara.org"]:
            texto_final = ""

        return {
            "estado": "exito",
            "archivo": audio.filename,
            "texto": texto_final,
            "idioma": resultado.get("language", "es")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error crítico en el motor de transcripción IA: {str(e)}")

    finally:
        # 4. Limpieza absoluta y segura del archivo temporal en el disco duro
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                print(f"[Warning] No se pudo eliminar el archivo temporal {tmp_path}: {e}")
