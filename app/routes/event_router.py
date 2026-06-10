# app/routes/event_router.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database.db import SessionLocal
from app.models.tarea import Tarea  # <- Cambiado aquí
from app.schemas.event_schema import EventOut

router = APIRouter(prefix="/events", tags=["Eventos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[EventOut])
def list_task_events(
    user_uid: str = Query(..., description="UID del usuario cuyas tareas convertimos en eventos"),
    db: Session = Depends(get_db)
):
    # Solo tareas activas asignadas a este usuario, con proyecto cargado para fecha
    tareas = (
        db.query(Tarea)
          .options(joinedload(Tarea.project))
          .filter(
             Tarea.assigned_user_uid == user_uid,
             Tarea.estado == True
          )
          .all()
    )

    events: List[EventOut] = []
    for t in tareas:
        day = t.project.start_date.isoformat()
        events.append(EventOut(
            id=f"task-{t.id}",
            title=f"✅ {t.title}",
            start=day,
            end=day,
            allDay=True
        ))

    return events

