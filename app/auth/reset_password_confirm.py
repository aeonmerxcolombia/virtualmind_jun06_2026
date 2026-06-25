from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import mysql.connector
import bcrypt
from mysql.connector import Error as MySQLError

router = APIRouter(
    prefix="/auth",
    tags=["Recuperar contraseña"]
)

# Conexión a la base de datos
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="catedra2025",
        database="virtualmind_db"
    )

# Modelo de datos
class ResetPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password-confirm")
def reset_password_confirm(data: ResetPasswordConfirmRequest):
    try:
        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:

                # Verifica el token y extrae el correo
                cursor.execute("SELECT email FROM password_reset_tokens WHERE token = %s", (data.token,))
                result = cursor.fetchone()

                if not result:
                    raise HTTPException(status_code=400, detail="Token inválido o expirado")

                email = result['email']

                # Verifica si el correo existe en la tabla usuarios
                cursor.execute("SELECT email FROM usuarios WHERE email = %s", (email,))
                user_exists = cursor.fetchone()

                if not user_exists:
                    raise HTTPException(status_code=400, detail="El usuario no existe")

                # Hashea la nueva contraseña
                hashed_password = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                # Actualiza la contraseña
                cursor.execute("UPDATE usuarios SET password = %s WHERE email = %s", (hashed_password, email))

                # Elimina el token usado
                cursor.execute("DELETE FROM password_reset_tokens WHERE token = %s", (data.token,))

                conn.commit()

        return {"message": "Contraseña actualizada correctamente"}

    except MySQLError as db_err:
        print(f"Error de MySQL: {repr(db_err)}")
        raise HTTPException(status_code=500, detail="Error en la base de datos")

    except Exception as e:
        print(f"Error inesperado: {repr(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

