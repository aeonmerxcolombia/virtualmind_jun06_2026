# app/auth/deps.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.jwt_handler import decodeJWT
from typing import List, Optional
from functools import wraps

oauth2_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> dict:
    token = credentials.credentials
    payload = decodeJWT(token)
    if not payload or "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def get_user_roles(payload: dict = Depends(get_current_user)) -> List[str]:
    return payload.get("roles", [])

def require_roles(required_roles: List[str]):
    def dependency(payload: dict = Depends(get_current_user)):
        user_roles = payload.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Roles requeridos: {', '.join(required_roles)}"
            )
        return payload
    return dependency

def require_auth(payload: dict = Depends(get_current_user)) -> dict:
    return payload
