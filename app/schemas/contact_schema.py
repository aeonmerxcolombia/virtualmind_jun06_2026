from pydantic import BaseModel, EmailStr

# Lo que envía el formulario web
class ContactCreate(BaseModel):
    nombre: str
    email: EmailStr
    asunto: str
    mensaje: str

    class Config:
        from_attributes = True

# Lo que usarás después para cambiar el correo de Hugo desde el admin
class UpdateContactEmail(BaseModel):
    new_email: EmailStr
