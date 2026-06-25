from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import aiosmtplib
import os

router = APIRouter(prefix="/auth", tags=["SMTP Test"])

class TestEmailRequest(BaseModel):
    email: EmailStr

@router.post("/send-test-email")
async def send_test_email(data: TestEmailRequest):
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

    message = f"""\
From: {SMTP_USER}
To: {data.email}
Subject: Prueba SMTP desde Virtualmind

Este es un correo de prueba para verificar configuración SMTP.
"""

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        return {"message": f"Correo de prueba enviado a {data.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al enviar correo: {e}")

