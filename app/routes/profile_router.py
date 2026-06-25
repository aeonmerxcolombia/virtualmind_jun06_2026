from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.profile import Profile
from app.schemas.profile_schema import ProfileOut
import uuid
import os

router = APIRouter(prefix="/profiles", tags=["Profiles"])
UPLOAD_DIR = "/home/ubuntu/backend/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=ProfileOut)
async def create_profile(
    user_id: str = Form(...),
    nombre: str = Form(None),
    apellidos: str = Form(None),
    telefono: str = Form(None),
    celular: str = Form(None),
    direccion: str = Form(None),
    ciudad: str = Form(None),
    pais: str = Form(None),
    cargo: str = Form(None),
    empresa: str = Form(None),
    biografia: str = Form(None),
    linkedin: str = Form(None),
    twitter: str = Form(None),
    facebook: str = Form(None),
    notificaciones_email: bool = Form(True),
    notificaciones_virtualmind: bool = Form(True),
    privacidad_perfil: str = Form("privado"),
    intereses_interes_principal: str = Form(None),
    intereses_formato_preferido: str = Form(None),
    intereses_nivel_experiencia: str = Form(None),
    intereses_objetivo_principal: str = Form(None),
    intereses_temas: str = Form(None),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    foto_url = None
    if foto:
        ext = os.path.splitext(foto.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            f.write(await foto.read())
        foto_url = f"https://gestordecursos.pegui.edu.co:8000/static/uploads/{filename}"

    profile = Profile(
        user_id=user_id,
        nombre=nombre,
        apellidos=apellidos,
        telefono=telefono,
        celular=celular,
        direccion=direccion,
        ciudad=ciudad,
        pais=pais,
        cargo=cargo,
        empresa=empresa,
        biografia=biografia,
        linkedin=linkedin,
        twitter=twitter,
        facebook=facebook,
        notificaciones_email=notificaciones_email,
        notificaciones_virtualmind=notificaciones_virtualmind,
        privacidad_perfil=privacidad_perfil,
        intereses_interes_principal=intereses_interes_principal,
        intereses_formato_preferido=intereses_formato_preferido,
        intereses_nivel_experiencia=intereses_nivel_experiencia,
        intereses_objetivo_principal=intereses_objetivo_principal,
        intereses_temas=intereses_temas,
        foto_url=foto_url
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{user_id}", response_model=ProfileOut)
def get_profile(user_id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return profile


@router.put("/{user_id}", response_model=ProfileOut)
async def update_profile(
    user_id: str,
    nombre: str = Form(None),
    apellidos: str = Form(None),
    telefono: str = Form(None),
    celular: str = Form(None),
    direccion: str = Form(None),
    ciudad: str = Form(None),
    pais: str = Form(None),
    cargo: str = Form(None),
    empresa: str = Form(None),
    biografia: str = Form(None),
    linkedin: str = Form(None),
    twitter: str = Form(None),
    facebook: str = Form(None),
    notificaciones_email: bool = Form(True),
    notificaciones_virtualmind: bool = Form(True),
    privacidad_perfil: str = Form("privado"),
    intereses_interes_principal: str = Form(None),
    intereses_formato_preferido: str = Form(None),
    intereses_nivel_experiencia: str = Form(None),
    intereses_objetivo_principal: str = Form(None),
    intereses_temas: str = Form(None),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    # Actualizar solo si se envían valores
    profile.nombre = nombre or profile.nombre
    profile.apellidos = apellidos or profile.apellidos
    profile.telefono = telefono or profile.telefono
    profile.celular = celular or profile.celular
    profile.direccion = direccion or profile.direccion
    profile.ciudad = ciudad or profile.ciudad
    profile.pais = pais or profile.pais
    profile.cargo = cargo or profile.cargo
    profile.empresa = empresa or profile.empresa
    profile.biografia = biografia or profile.biografia
    profile.linkedin = linkedin or profile.linkedin
    profile.twitter = twitter or profile.twitter
    profile.facebook = facebook or profile.facebook
    profile.notificaciones_email = notificaciones_email
    profile.notificaciones_virtualmind = notificaciones_virtualmind
    profile.privacidad_perfil = privacidad_perfil
    profile.intereses_interes_principal = intereses_interes_principal or profile.intereses_interes_principal
    profile.intereses_formato_preferido = intereses_formato_preferido or profile.intereses_formato_preferido
    profile.intereses_nivel_experiencia = intereses_nivel_experiencia or profile.intereses_nivel_experiencia
    profile.intereses_objetivo_principal = intereses_objetivo_principal or profile.intereses_objetivo_principal
    profile.intereses_temas = intereses_temas or profile.intereses_temas

    if foto:
        ext = os.path.splitext(foto.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            f.write(await foto.read())
        profile.foto_url = f"https://gestordecursos.pegui.edu.co:8000/static/uploads/{filename}"

    db.commit()
    db.refresh(profile)
    return profile

