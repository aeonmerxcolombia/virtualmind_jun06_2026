from fastapi import APIRouter, Depends, HTTPException
from app.auth.deps import get_current_user
from pydantic import BaseModel
import mysql.connector

router = APIRouter()

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "catedra2025"
DB_NAME = "virtualmind_db"

class ChatClienteRequest(BaseModel):
    mensaje: str

@router.post("/chat/cliente/inteligencia")
async def ia_cliente(
    datos: ChatClienteRequest,
    current_user: dict = Depends(get_current_user)
):
    mensaje = datos.mensaje.lower()
    user_uid = current_user.get("user_id")  # este debe coincidir con user_uid en DB

    if not user_uid:
        raise HTTPException(status_code=401, detail="Token inválido: no se encontró user_id")

    if "proyecto" in mensaje:
        return {"respuesta": listar_proyectos(user_uid)}
    elif "tarea" in mensaje:
        return {"respuesta": listar_tareas(user_uid)}
    elif "resumen" in mensaje:
        return {"respuesta": resumen_general(user_uid)}
    else:
        return {
            "respuesta": "🤖 No entendí tu pregunta. Puedes preguntar por 'proyectos', 'tareas' o pedir un 'resumen general'."
        }

def listar_proyectos(user_id):
    try:
        with mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        ) as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT DISTINCT p.id, p.name, p.estado
                    FROM projects p
                    JOIN tasks t ON t.project_id = p.id
                    WHERE t.assigned_user_uid = %s
                """, (user_id,))
                rows = cursor.fetchall()
                if not rows:
                    return "📂 No tienes proyectos registrados."
                return "\n".join([f"📁 {row['name']} – Estado: {row['estado']}" for row in rows])
    except Exception as e:
        return f"❌ Error al consultar proyectos: {e}"


def listar_tareas(user_uid):
    try:
        with mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        ) as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT title, estado FROM tasks
                    WHERE assigned_user_uid = %s
                """, (user_uid,))
                rows = cursor.fetchall()
                if not rows:
                    return "✅ No tienes tareas asignadas."
                return "\n".join([f"📝 {row['title']} – {row['estado']}" for row in rows])
    except Exception as e:
        return f"❌ Error al consultar tareas: {e}"


def resumen_general(user_uid):
    return listar_proyectos(user_uid) + "\n\n" + listar_tareas(user_uid)

