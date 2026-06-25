# app/auth/password_recovery.py

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.database.db import get_db
from sqlalchemy import text
import aiosmtplib
import os
import secrets
from email.message import EmailMessage
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["Recuperar contraseña"])

class PasswordRecoveryRequest(BaseModel):
    email: EmailStr

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

class ResetPasswordRequest(BaseModel):
    email: str
    reset_token: str
    new_password: str

async def send_reset_code_email(email_to: str, code: str):
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Virtualmind")

    message = EmailMessage()
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    message["To"] = email_to
    message["Subject"] = "Código de verificación - VirtualMind"
    message.set_content(f"""¡Hola!

Has solicitado restablecer tu contraseña en VirtualMind.

Tu código de verificación es:

        {code}

Este código expira en 15 minutos.

Si no solicitaste este correo, puedes ignorarlo de safely.

Saludos,
El equipo de VirtualMind""")

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
    except Exception as e:
        print(f"Error enviando correo: {e}")
        raise e

def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)

def generate_6digit_code() -> str:
    return ''.join(secrets.choice('0123456789') for _ in range(6))

@router.post("/request-password-reset")
async def request_password_reset(
    data: PasswordRecoveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    query = text("SELECT * FROM usuarios WHERE email = :email")
    user = db.execute(query, {"email": data.email}).fetchone()
    if not user:
        return {"message": "Si el correo existe, recibirás un email con instrucciones."}

    # Verificar si ya hay un código reciente no usado (menos de 2 minutos)
    check_recent = text("""
        SELECT * FROM password_reset_tokens 
        WHERE email = :email AND used = 0 AND expires_at > NOW() AND created_at > DATE_SUB(NOW(), INTERVAL 2 MINUTE)
    """)
    recent = db.execute(check_recent, {"email": data.email}).fetchone()
    if recent:
        return {"message": "Ya se envió un código recientemente. Espera 2 minutos para solicitar otro."}

    code = generate_6digit_code()
    reset_token = generate_password_reset_token()
    expires_at = datetime.now() + timedelta(minutes=15)

    # Eliminar códigos anteriores del usuario
    delete_old = text("DELETE FROM password_reset_tokens WHERE email = :email")
    db.execute(delete_old, {"email": data.email})

    # Guardar nuevo código
    insert_query = text("""
        INSERT INTO password_reset_tokens (email, token, code, expires_at, used) 
        VALUES (:email, :token, :code, :expires_at, 0)
    """)
    db.execute(insert_query, {
        "email": data.email, 
        "token": reset_token,
        "code": code,
        "expires_at": expires_at
    })
    db.commit()

    background_tasks.add_task(send_reset_code_email, data.email, code)

    return {"message": "Código enviado correctamente", "email": data.email}

@router.post("/verify-password-reset-code")
async def verify_password_reset_code(
    data: VerifyCodeRequest,
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT * FROM password_reset_tokens 
        WHERE email = :email AND code = :code AND used = 0 AND expires_at > NOW()
        ORDER BY created_at DESC LIMIT 1
    """)
    record = db.execute(query, {"email": data.email, "code": data.code}).fetchone()
    
    if not record:
        raise HTTPException(status_code=400, detail="Código inválido o expirado")

    # Marcar como usado parcialmente
    update = text("UPDATE password_reset_tokens SET used = 1 WHERE id = :id")
    db.execute(update, {"id": record.id})
    db.commit()

    return {"message": "Código verificado", "reset_token": record.token}

@router.post("/reset-password-confirm")
async def reset_password_confirm(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    # Verificar que el token sea válido
    query = text("""
        SELECT * FROM password_reset_tokens 
        WHERE email = :email AND token = :token AND used = 1
        ORDER BY created_at DESC LIMIT 1
    """)
    record = db.execute(query, {"email": data.email, "token": data.reset_token}).fetchone()
    
    if not record:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    # Actualizar contraseña
    import bcrypt
    hashed = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    update_user = text("UPDATE usuarios SET password = :password WHERE email = :email")
    db.execute(update_user, {"password": hashed, "email": data.email})
    
    # Eliminar token usado
    delete_token = text("DELETE FROM password_reset_tokens WHERE id = :id")
    db.execute(delete_token, {"id": record.id})
    
    db.commit()

    return {"message": "Contraseña actualizada correctamente"}



