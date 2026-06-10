from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.auth.hashing import Hash
import pandas as pd
import io
import uuid

router = APIRouter(prefix="/bulk", tags=["Carga Masiva de Usuarios"])

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/usuarios")
async def cargar_usuarios_desde_excel(archivo: UploadFile = File(...), db: Session = Depends(get_db)):
    if not archivo.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Debe subir un archivo Excel (.xlsx o .xls)")

    contenido = await archivo.read()
    try:
        df = pd.read_excel(io.BytesIO(contenido))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error leyendo el Excel: " + str(e))

    usuarios_creados = []
    errores = []

    for i, fila in df.iterrows():
        try:
            email = str(fila['email']).strip().lower()
            if db.query(User).filter(User.email == email).first():
                errores.append({"fila": i + 2, "error": f"Email {email} ya registrado"})
                continue

            role_ids = [int(r.strip()) for r in str(fila['role_ids']).split(',') if r.strip().isdigit()]
            roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
            if not roles or len(roles) != len(role_ids):
                errores.append({"fila": i + 2, "error": f"Uno o más roles no existen: {role_ids}"})
                continue

            nuevo_usuario = User(
                uid=str(uuid.uuid4()),
                nombre=str(fila['nombre']).strip(),
                tipo_documento=str(fila['tipo_documento']).strip(),
                documento=str(fila['documento']).strip(),
                email=email,
                password=Hash.encrypt(str(fila['password']).strip()),
                estado=True,
                roles=roles
            )
            db.add(nuevo_usuario)
            db.commit()
            usuarios_creados.append(email)
        except Exception as e:
            errores.append({"fila": i + 2, "error": str(e)})
            db.rollback()

    return {
        "usuarios_creados": usuarios_creados,
        "errores": errores
    }

