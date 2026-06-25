
from pydantic import BaseModel
from typing import List

# Para crear un permiso
class PermissionCreate(BaseModel):
    name: str

# Para devolver un permiso
class PermissionOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# Para crear o actualizar un rol
class RoleCreate(BaseModel):
    name: str
    permission_ids: List[int] = []

# Para devolver un rol con sus permisos anidados
class RoleOut(BaseModel):
    id: int
    name: str
    permissions: List[PermissionOut] = []

    class Config:
        from_attributes = True

