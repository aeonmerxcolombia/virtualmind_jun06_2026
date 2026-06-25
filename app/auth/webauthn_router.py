import os
import json
import base64

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.database.db import SessionLocal
from app.models.user import User
from app.models.webauthn_credential import WebAuthnCredential
from app.auth.jwt_handler import create_access_token

from webauthn import generate_registration_options, verify_registration_response
from webauthn import generate_authentication_options, verify_authentication_response
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    ResidentKeyRequirement,
    PublicKeyCredentialDescriptor,
)
from webauthn.helpers.options_to_json import options_to_json

router = APIRouter(
    prefix="/auth/webauthn",
    tags=["Autenticación por Huella Dactilar (WebAuthn)"]
)

RP_ID = "gestordecursos.pegui.edu.co"
RP_NAME = "Virtualmind"
ORIGIN = "https://gestordecursos.pegui.edu.co"

_challenge_store: dict = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class BeginRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    device_name: str = ""


class BeginRegisterResponse(BaseModel):
    publicKey: dict


@router.post("/register/begin")
def webauthn_register_begin(
    request: BeginRegisterRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    from app.auth.hashing import Hash
    if not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    existing = db.query(WebAuthnCredential).filter(
        WebAuthnCredential.user_uid == user.uid
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya tienes una huella registrada")

    user_id_bytes = user.uid.encode("utf-8")

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user_id_bytes,
        user_name=user.email,
        user_display_name=user.nombre,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.REQUIRED,
            resident_key=ResidentKeyRequirement.PREFERRED,
        ),
    )

    challenge_id = str(id(options.challenge))
    _challenge_store[user.email] = {
        "challenge": options.challenge,
        "device_name": request.device_name,
    }

    return JSONResponse(content=json.loads(options_to_json(options)))


class CompleteRegisterRequest(BaseModel):
    email: EmailStr
    credential: dict


@router.post("/register/complete")
def webauthn_register_complete(
    request: CompleteRegisterRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    stored = _challenge_store.pop(request.email, None)
    if not stored:
        raise HTTPException(status_code=400, detail="No se encontró desafío pendiente. Reintenta.")

    from webauthn.helpers.structs import RegistrationCredential

    try:
        credential = RegistrationCredential.from_json(json.dumps(request.credential))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Credencial inválida: {str(e)}")

    try:
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=stored["challenge"],
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error verificando credencial: {str(e)}")

    new_cred = WebAuthnCredential(
        user_uid=user.uid,
        credential_id=verification.credential_id.hex(),
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        device_name=stored["device_name"],
    )
    db.add(new_cred)
    db.commit()

    return {"status": "ok", "message": "Huella dactilar registrada exitosamente"}


class BeginLoginRequest(BaseModel):
    email: EmailStr


@router.post("/login/begin")
def webauthn_login_begin(
    request: BeginLoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    creds = db.query(WebAuthnCredential).filter(
        WebAuthnCredential.user_uid == user.uid
    ).all()
    if not creds:
        raise HTTPException(status_code=400, detail="No tienes una huella registrada")

    allow_credentials = [
        PublicKeyCredentialDescriptor(id=bytes.fromhex(c.credential_id))
        for c in creds
    ]

    options = generate_authentication_options(
        rp_id=RP_ID,
        user_verification=UserVerificationRequirement.REQUIRED,
        allow_credentials=allow_credentials,
    )

    _challenge_store[f"login:{request.email}"] = {
        "challenge": options.challenge,
    }

    return JSONResponse(content=json.loads(options_to_json(options)))


class CompleteLoginRequest(BaseModel):
    email: EmailStr
    credential: dict


@router.post("/login/complete")
def webauthn_login_complete(
    request: CompleteLoginRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.estado:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    stored = _challenge_store.pop(f"login:{request.email}", None)
    if not stored:
        raise HTTPException(status_code=400, detail="No se encontró desafío pendiente. Reintenta.")

    raw_id = request.credential.get("id", "")
    try:
        cred_id_bytes = base64.urlsafe_b64decode(raw_id + "==")
        credential_id_hex = cred_id_bytes.hex()
    except Exception:
        credential_id_hex = raw_id
    cred = db.query(WebAuthnCredential).filter(
        WebAuthnCredential.credential_id == credential_id_hex
    ).first()
    if not cred:
        raise HTTPException(status_code=400, detail="Credencial no encontrada en el servidor")

    from webauthn.helpers.structs import AuthenticationCredential

    try:
        auth_cred = AuthenticationCredential.from_json(json.dumps(request.credential))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Credencial inválida: {str(e)}")

    try:
        verification = verify_authentication_response(
            credential=auth_cred,
            expected_challenge=stored["challenge"],
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=cred.public_key,
            credential_current_sign_count=cred.sign_count,
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Verificación fallida: {str(e)}")

    cred.sign_count = verification.new_sign_count
    db.commit()

    access_token = create_access_token(data={
        "sub": user.email,
        "nombre": user.nombre,
        "roles": [r.name for r in user.roles],
        "permissions": [p.name for r in user.roles for p in r.permissions],
        "user_id": user.uid,
    })

    terminos_aceptados_bool = user.terms_accepted_at is not None

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "terms_accepted": terminos_aceptados_bool,
    }


class StatusRequest(BaseModel):
    email: EmailStr

@router.post("/status")
def webauthn_status(request: StatusRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    creds = db.query(WebAuthnCredential).filter(
        WebAuthnCredential.user_uid == user.uid
    ).count()
    return {"registered": creds > 0}
