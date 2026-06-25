import itertools
from google import genai

from app.colmena.config import settings

_gemini_keys = settings.GEMINI_API_KEYS
_key_cycle = itertools.cycle(_gemini_keys) if _gemini_keys else iter([])


def get_gemini_key() -> str:
    try:
        return next(_key_cycle)
    except StopIteration:
        return ""


def get_gemini_client():
    key = get_gemini_key()
    if not key:
        return None
    return genai.Client(api_key=key)
