import os
import hmac
import hashlib
import json
import base64
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import jwt, JWTError
from fastapi import HTTPException, WebSocket, status, Request, Depends
from app.colmena.config import settings
from app.auth.jwt_handler import decodeJWT


@dataclass
class AgentContext:
    user_id: int
    email: str
    nombre: str
    roles: List[str]
    permissions: List[str] = field(default_factory=list)
    token: str = ""


async def get_current_agent_context(token: str) -> AgentContext:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    payload = decodeJWT(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    return AgentContext(
        user_id=payload.get("user_id"),
        email=payload.get("sub", ""),
        nombre=payload.get("nombre", ""),
        roles=payload.get("roles", []),
        permissions=payload.get("permissions", []),
    )


async def get_ws_agent_context(websocket: WebSocket) -> Optional[AgentContext]:
    token = websocket.query_params.get("token")
    if not token:
        return None
    payload = decodeJWT(token)
    if not payload:
        return None
    return AgentContext(
        user_id=payload.get("user_id"),
        email=payload.get("sub", ""),
        nombre=payload.get("nombre", ""),
        roles=payload.get("roles", []),
        permissions=payload.get("permissions", []),
        token=token,
    )


async def get_current_agent_dep(request: Request) -> AgentContext:
    auth = request.headers.get("Authorization")
    token = auth.replace("Bearer ", "") if auth else request.query_params.get("token")
    return await get_current_agent_context(token)


async def get_token_from_header(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth else request.query_params.get("token", "")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    return token


def require_permission(required_permission: str):
    async def _permission_checker(context: AgentContext = Depends(get_current_agent_dep)):
        if required_permission not in context.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: se requiere permiso '{required_permission}'"
            )
        return context
    return _permission_checker


def check_ws_permission(context: AgentContext, required_permission: str) -> bool:
    return required_permission in context.permissions

class CryptoAdnGuard:
    @staticmethod
    def sign_code(file_path: str) -> str:
        hmac_hash = hmac.new(settings.CODE_SIGN_KEY.encode(), digestmod=hashlib.sha256)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo de código no encontrado: {file_path}")
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                hmac_hash.update(byte_block)
        return hmac_hash.hexdigest()

    @staticmethod
    def verify_file_integrity(file_path: str, expected_signature: str) -> bool:
        if not os.path.exists(file_path):
            return False
        current_sig = CryptoAdnGuard.sign_code(file_path)
        return hmac.compare_digest(current_sig, expected_signature)


class WebSocketSymmetricRotator:
    def __init__(self, raw_secret: str):
        self.key = hashlib.sha256(raw_secret.encode()).digest()
        self.aesgcm = AESGCM(self.key)

    def encrypt(self, plain_text: str) -> str:
        nonce = os.urandom(12)
        encrypted_bytes = self.aesgcm.encrypt(nonce, plain_text.encode(), None)
        return base64.b64encode(nonce + encrypted_bytes).decode('utf-8')

    def decrypt(self, encrypted_base64: str) -> str:
        data = base64.b64decode(encrypted_base64)
        nonce = data[:12]
        encrypted_bytes = data[12:]
        decrypted_bytes = self.aesgcm.decrypt(nonce, encrypted_bytes, None)
        return decrypted_bytes.decode('utf-8')


class ShadowGuardrail:
    @staticmethod
    async def validate_semantic_safety(command: str, role: str) -> bool:
        import httpx
        payload = {
            "model": "qwen2.5-coder:1.5b-instruct-q4_K_M",
            "prompt": f"Analiza el siguiente comando emitido por el rol {role}. Responde estrictamente con un JSON: {{\"safe\": true}} o {{\"safe\": false}}. Comando: {command}",
            "stream": False,
            "format": "json"
        }
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.post(settings.OLLAMA_URL, json=payload)
                if response.status_code == 200:
                    res_json = response.json()
                    parsed_res = json.loads(res_json.get("response", "{}"))
                    return parsed_res.get("safe", True)
        except Exception:
            return True
        return True


class LymphocyteBehavioralMonitor:
    def __init__(self):
        self.banned_ips = set()
        self.request_timestamps = {}

    def is_banned(self, ip_address: str) -> bool:
        return ip_address in self.banned_ips

    def audit_traffic(self, ip_address: str):
        now = datetime.now().timestamp()
        if ip_address not in self.request_timestamps:
            self.request_timestamps[ip_address] = []
        timestamps = self.request_timestamps[ip_address]
        self.request_timestamps[ip_address] = [t for t in timestamps if now - t < 10]
        self.request_timestamps[ip_address].append(now)
        if len(self.request_timestamps[ip_address]) > 50:
            print(f"[LINFOCITO] Anomalía detectada en la IP: {ip_address}. Baneo activo.")
            self.banned_ips.add(ip_address)
