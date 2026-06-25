import json
from typing import Any, Dict, List, Optional

from app.services.ai.gemini_pool import get_gemini_client


def generate_with_ai(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    client = get_gemini_client()
    if not client:
        return json.dumps({"error": "No hay API keys de Gemini disponibles"})

    try:
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=config,
        )

        return response.text
    except Exception as e:
        return json.dumps({"error": str(e)})


def generate_json_with_ai(
    prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.3
) -> Dict[str, Any]:
    client = get_gemini_client()
    if not client:
        return {"error": "No hay API keys de Gemini disponibles"}

    try:
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=4096,
            system_instruction=system_instruction,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=config,
        )

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}
