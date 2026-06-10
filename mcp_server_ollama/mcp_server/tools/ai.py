import os
import json
from typing import Any, Dict, List, Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def generate_with_ai(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> str:
    """Genera contenido usando Gemini API."""
    if not GEMINI_API_KEY:
        return json.dumps({"error": "GEMINI_API_KEY no configurada"})
    
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
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
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """Genera JSON usando Gemini API."""
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY no configurada"}
    
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=4096,
            system_instruction=system_instruction,
            response_mime_type="application/json",
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=config,
        )
        
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw": generate_with_ai(prompt, system_instruction, temperature)}
    except Exception as e:
        return {"error": str(e)}
