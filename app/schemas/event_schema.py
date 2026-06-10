from pydantic import BaseModel
from typing import Optional

class EventOut(BaseModel):
    id:     str     # usamos string para distinguir "proj-1" vs "task-3"
    title:  str
    start:  str     # ISO date: "2025-06-01"
    end:    Optional[str] = None
    allDay: bool   = True

    class Config:
        # Pydantic v2: usar from_attributes en lugar de orm_mode
        from_attributes = True

