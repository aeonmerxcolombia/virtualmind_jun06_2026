from pydantic import BaseModel
from typing import Optional

class ProyectoParticipanteBase(BaseModel):
    project_id: int
    user_uid: str
    role_id: int = 1

class ProyectoParticipanteCreate(ProyectoParticipanteBase):
    pass

class ProyectoParticipanteRead(ProyectoParticipanteBase):
    id: int

    class Config:
        from_attributes = True
