# app/routes/log_router.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services import log_service
from app.database.db import get_db

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.get("/")
def ver_logs(db: Session = Depends(get_db)):
    return log_service.obtener_logs(db)

