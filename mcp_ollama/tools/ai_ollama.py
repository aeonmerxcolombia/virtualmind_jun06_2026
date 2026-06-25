import json
import os
import requests
from typing import Any, Dict, Optional

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def generate_with_ai(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> str:
    payload = {
        "model": "llama3.2:latest",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }
    if system_instruction:
        payload["system"] = system_instruction
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return json.dumps({"error": str(e)})

def generate_json_with_ai(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.3
) -> Dict[str, Any]:
    payload = {
        "model": "llama3.2:latest",
        "prompt": prompt + "\n\nResponde ÚNICAMENTE con JSON válido, sin explicaciones adicionales.",
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 4096
        }
    }
    if system_instruction:
        payload["system"] = system_instruction
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        text = response.json().get("response", "")
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0]
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw": generate_with_ai(prompt, system_instruction, temperature)}
    except Exception as e:
        return {"error": str(e)}
