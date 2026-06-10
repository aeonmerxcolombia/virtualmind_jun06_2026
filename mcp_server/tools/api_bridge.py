"""
MCP ApiBridge Adapter — Wraps the backend ApiBridge for MCP Server tools.
When a JWT token is available, tools call the real API endpoints instead of using direct DB.
"""
import sys
sys.path.insert(0, '/home/ubuntu/backend')

from typing import Any, Dict, List, Optional
from app.colmena.api_bridge import ApiBridge, ApiBridgeError


def create_bridge(token: str = None) -> Optional[ApiBridge]:
    if not token:
        return None
    return ApiBridge(token=token, base_url="https://localhost:8000")


# Convenience wrappers for MCP tools

def safe_call(bridge: Optional[ApiBridge], method_name: str, *args, **kwargs) -> Any:
    if bridge:
        method = getattr(bridge, method_name, None)
        if method:
            try:
                return method(*args, **kwargs)
            except ApiBridgeError as e:
                return e.to_dict()
    return None
