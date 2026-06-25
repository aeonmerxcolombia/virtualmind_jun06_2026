# app/services/ai/mcp_service.py
import json
import itertools
from typing import Optional, Dict, Any, List
from google.genai import types
from google import genai
from app.colmena.config import settings


class MCPService:
    def __init__(self):
        self.api_keys = settings.GEMINI_API_KEYS
        self.model_fast = settings.MODEL_FAST
        self.model_complex = settings.MODEL_COMPLEX
        self.model_embedding = settings.MODEL_EMBEDDING
        self.available = len(self.api_keys) > 0
        self._key_cycle = itertools.cycle(self.api_keys) if self.api_keys else iter([])

    def _get_client(self):
        api_key = next(self._key_cycle)
        return genai.Client(api_key=api_key)

    def _check_available(self):
        if not self.available:
            raise RuntimeError(
                "No hay API Keys de Gemini configuradas. "
                "Revisa GEMINI_API_KEYS en app/colmena/config.py"
            )

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: Optional[str] = None,
    ) -> str:
        self._check_available()
        client = self._get_client()
        model_name = model or self.model_fast
        contents = [prompt]

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

        return response.text

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._check_available()
        client = self._get_client()
        model_name = model or self.model_fast
        contents = [prompt]

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
            response_mime_type="application/json",
        )

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": response.text}

    def generate_complex(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 8192,
    ) -> str:
        return self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
            model=self.model_complex,
        )

    def analyze(
        self,
        content: str,
        analysis_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        from app.services.ai.prompts import get_analysis_prompt

        prompt = get_analysis_prompt(analysis_type, content, context)

        return self.generate_json(
            prompt=prompt,
            system_instruction="Eres un asistente de IA especializado en análisis educativo y pedagógico. Responde siempre en JSON válido.",
            temperature=0.3
        )

    def generate_content(
        self,
        entity_type: str,
        context: Dict[str, Any],
        action: str = "generate"
    ) -> Dict[str, Any]:
        from app.services.ai.prompts import get_generation_prompt

        prompt = get_generation_prompt(entity_type, context, action)

        return self.generate_json(
            prompt=prompt,
            system_instruction="Eres un asistente de IA especializado en diseño educativo y creación de contenido. Responde siempre en JSON válido.",
            temperature=0.7
        )

    def improve_content(
        self,
        content: str,
        entity_type: str,
        improvement_type: str = "general"
    ) -> Dict[str, Any]:
        from app.services.ai.prompts import get_improvement_prompt

        prompt = get_improvement_prompt(content, entity_type, improvement_type)

        return self.generate_json(
            prompt=prompt,
            system_instruction="Eres un experto en mejora de contenido educativo. Mejora el texto manteniendo el sentido original. Responde siempre en JSON válido.",
            temperature=0.5
        )


mcp_service = MCPService()
