from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ResourceBase(BaseModel):
    title: str
    description: Optional[str] = None
    file_type: str
    category: Optional[str] = None
    tags: Optional[str] = None

class ResourceFromUrl(BaseModel):
    file_url: str
    title: str
    file_type: str
    category: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    thumbnail_url: Optional[str] = None

class ResourceOut(ResourceBase):
    id: int
    file_url: str
    thumbnail_url: Optional[str] = None
    created_at: datetime
    owner_id: Optional[str]

    class Config:
        orm_mode = True

