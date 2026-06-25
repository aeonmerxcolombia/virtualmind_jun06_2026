from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
# Asegúrate de importar tus modelos y esquemas
from app.models.contact_model import ContactMessage, Configuracion
from app.schemas.contact_schema import ContactCreate, UpdateContactEmail
import os
import aiosmtplib
from email.message import EmailMessage

router = APIRouter(
    prefix="/public",
    tags=["Contacto"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FUNCIÓN DE ENVÍO DE CORREO (ASÍNCRONA) ---
async def send_contact_email_async(destinatario: str, datos: ContactCreate):
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Virtualmind Web")
    
    msg = EmailMessage()
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = destinatario
    msg["Reply-To"] = datos.email  # Para que al dar 'Responder' le llegue al usuario
    msg["Subject"] = f"[Contacto Web] {datos.asunto}"
    
    body = f"""
    Hola,
    
    Has recibido un nuevo mensaje desde el formulario de contacto de Virtualmind.
    
    --------------------------------------------------
    👤 Nombre: {datos.nombre}
    📧 Email:  {datos.email}
    📝 Asunto: {datos.asunto}
    --------------------------------------------------
    
    MENSAJE:
    {datos.mensaje}
    
    --------------------------------------------------
    Este mensaje ha sido guardado en la base de datos de auditoría.
    """
    msg.set_content(body)

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True
        )
        print(f"Correo de contacto enviado exitosamente a {destinatario}")
    except Exception as e:
        print(f"ERROR CRÍTICO enviando correo a {destinatario}: {e}")



# --- ENDPOINT NUEVO: OBTENER CORREO ACTUAL (GET) ---
@router.get("/config/email")
def get_contact_config(db: Session = Depends(get_db)):
    config_entry = db.query(Configuracion).filter(Configuracion.clave == "contact_email").first()
    
    if not config_entry:
        return {"email": "No configurado"}
    
    return {"email": config_entry.valor}




# --- ENDPOINT 1: ENVIAR MENSAJE (PÚBLICO) ---
@router.post("/contact")
async def create_contact_message(
    contact_data: ContactCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # 1. Guardar mensaje en BD (Historial)
    new_message = ContactMessage(
        nombre=contact_data.nombre,
        email=contact_data.email,
        asunto=contact_data.asunto,
        mensaje=contact_data.mensaje
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # 2. Obtener el correo destino dinámicamente
    config = db.query(Configuracion).filter(Configuracion.clave == "contact_email").first()
    
    # Fallback por seguridad si no existe la config
    destinatario = config.valor if config else "hugolondono@catedra.edu.co"

    # 3. Enviar correo en Background (No bloquea la respuesta al usuario)
    background_tasks.add_task(send_contact_email_async, destinatario, contact_data)

    return {"message": "Mensaje enviado y registrado correctamente"}

# --- ENDPOINT 2: CAMBIAR CORREO DESTINO (SUPERADMIN) ---
@router.put("/config/email")
def update_contact_config(data: UpdateContactEmail, db: Session = Depends(get_db)):
    # TODO: Agregar validación de token/rol aquí
    
    config = db.query(Configuracion).filter(Configuracion.clave == "contact_email").first()
    if not config:
        config = Configuracion(clave="contact_email", valor=data.new_email, descripcion="Correo contacto")
        db.add(config)
    else:
        config.valor = data.new_email
    
    db.commit()
    return {"message": f"Correo de contacto actualizado a: {data.new_email}"}
