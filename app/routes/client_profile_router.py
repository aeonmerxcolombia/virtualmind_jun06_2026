# app/routes/client_profile_router.py

# --- CAMBIO: Se añaden más importaciones necesarias ---
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database.db import get_db
from app.models.client_profile import ClientProfile
# --- CAMBIO: Se importa el nuevo esquema de actualización ---
from app.schemas.client_profile_schema import ClientProfileCreate, ClientProfileOut, ClientProfileUpdate

router = APIRouter(prefix="/client-profiles", tags=["Client Profiles"])

@router.post("/", response_model=ClientProfileOut)
def create_client_profile(request: ClientProfileCreate, db: Session = Depends(get_db)):
    # Esta función está bien, el router de clientes la usará.
    client = ClientProfile(id=str(uuid.uuid4()), **request.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

# --- CAMBIO: SE AGREGA EL ENDPOINT PARA LISTAR TODOS LOS PERFILES ---
@router.get("/", response_model=List[ClientProfileOut], summary="Listar todos los perfiles de clientes")
def list_all_client_profiles(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10000  # Límite alto para la verificación de NIT duplicado
):
    """
    Obtiene una lista de todos los perfiles de clientes.
    Este endpoint soluciona el error "Method Not Allowed" y es necesario
    para la validación de NITs duplicados en el frontend.
    """
    profiles = db.query(ClientProfile).offset(skip).limit(limit).all()
    return profiles

@router.get("/{user_id}", response_model=ClientProfileOut)
def get_client_profile(user_id: str, db: Session = Depends(get_db)):
    # Esta función está bien, no necesita cambios.
    client = db.query(ClientProfile).filter(ClientProfile.user_id == user_id).first()
    if not client:
        raise HTTPException(404, "Perfil de cliente no encontrado")
    return client

# --- CAMBIO: SE MEJORA EL ENDPOINT DE ACTUALIZACIÓN ---
@router.put("/{user_id}", response_model=ClientProfileOut)
def update_client_profile(user_id: str, request: ClientProfileUpdate, db: Session = Depends(get_db)):
    """
    Actualiza el perfil de un cliente.
    - Usa el esquema ClientProfileUpdate para permitir actualizaciones parciales.
    - Solo actualiza los campos que se envían en la petición.
    """
    client = db.query(ClientProfile).filter(ClientProfile.user_id == user_id).first()
    if not client:
        raise HTTPException(404, "Perfil de cliente no encontrado")
    
    # Usamos exclude_unset=True para obtener solo los datos que el cliente envió
    update_data = request.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(client, key, value)
    
    db.commit()
    db.refresh(client)
    return client
