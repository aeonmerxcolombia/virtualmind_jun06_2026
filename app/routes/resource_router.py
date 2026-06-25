import base64
import httpx
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
import os, uuid
from typing import List, Optional

from app.database.db import SessionLocal
from app.auth.jwt_handler import verify_token
from app.models.resource import Resource, ResourceType
from app.schemas.resource_schema import ResourceOut, ResourceFromUrl

router = APIRouter(
    prefix="/resources",
    tags=["Biblioteca"]
)

# Mapping tipos MIME a categorías
TYPE_TO_CATEGORY = {
    "image/jpeg": "fotos",
    "image/jpg": "fotos", 
    "image/png": "fotos",
    "image/gif": "fotos",
    "image/webp": "fotos",
    "image/svg+xml": "vectores",
    "application/pdf": "documentos",
    "video/mp4": "videos",
    "video/webm": "videos",
    "audio/mpeg": "audios",
    "audio/wav": "audios",
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 📌 Subir recurso con categoría automática
@router.post("/", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def upload_resource(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    ext = os.path.splitext(file.filename)[1]
    name = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, name)

    with open(path, "wb") as f:
        f.write(await file.read())

    url = f"https://gestordecursos.pegui.edu.co:8000/static/resources/biblioteca/{name}"

    # Auto-detectar tipo y categoría
    content_type = file.content_type or ""
    if "pdf" in content_type:
        ftype = ResourceType.pdf
    elif "image" in content_type:
        ftype = ResourceType.image
        if content_type == "image/svg+xml":
            ftype = ResourceType.image  # vectores como imagen
    elif "video" in content_type:
        ftype = ResourceType.video
    elif "audio" in content_type:
        ftype = ResourceType.audio
    else:
        raise HTTPException(400, detail="Tipo de archivo no soportado")

    # Auto-categoría si no especificada
    if not category:
        category = TYPE_TO_CATEGORY.get(content_type, "documentos")

    resource = Resource(
        title=title,
        description=description,
        file_url=url,
        file_type=ftype,
        category=category,
        tags=tags,
        owner_id=token_data["user_id"],
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    return resource

# 📌 Listar con filtros por tipo y categoría
@router.get("/", response_model=List[ResourceOut])
def list_resources(
    type: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    q = db.query(Resource)
    if type:
        q = q.filter(Resource.file_type == type)
    if category:
        q = q.filter(Resource.category == category)
    if search:
        q = q.filter(Resource.title.ilike(f"%{search}%") | Resource.description.ilike(f"%{search}%"))
    return q.order_by(Resource.created_at.desc()).all()

# 📌 Obtener recursos por categoría
@router.get("/category/{category}", response_model=List[ResourceOut])
def get_by_category(
    category: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    return db.query(Resource).filter(Resource.category == category).order_by(Resource.created_at.desc()).all()

# 📌 Obtener estadísticas por categoría
@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    from sqlalchemy import func
    stats = db.query(
        Resource.category,
        func.count(Resource.id).label("count")
    ).group_by(Resource.category).all()
    return {s.category: s.count for s in stats}

UPLOAD_DIR = "/home/ubuntu/backend/static/resources/biblioteca"
os.makedirs(UPLOAD_DIR, exist_ok=True)

FILE_TYPE_MAP = {
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".gif": "image",
    ".webp": "image", ".svg": "image", ".bmp": "image",
    ".mp4": "video", ".webm": "video", ".mov": "video", ".avi": "video",
    ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".m4a": "audio",
    ".glb": "model", ".gltf": "model", ".obj": "model", ".fbx": "model",
    ".pdf": "pdf",
}

CATEGORY_MAP = {
    "image": "fotos",
    "video": "videos",
    "audio": "audios",
    "model": "ilustraciones",
    "pdf": "documentos",
}

@router.post("/from-url", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def create_resource_from_url(
    data: ResourceFromUrl,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token),
):
    url = data.file_url
    content = None
    content_type = ""

    if url.startswith("data:"):
        try:
            header, encoded = url.split(",", 1)
            content = base64.b64decode(encoded)
            content_type = header.replace("data:", "").split(";")[0]
        except Exception as e:
            raise HTTPException(400, detail=f"Error decoding base64: {e}")
    else:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                content = resp.content
                content_type = resp.headers.get("content-type", "")
        except Exception as e:
            raise HTTPException(400, detail=f"No se pudo descargar el archivo: {e}")

    ext_map = {
        "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
        "image/webp": ".webp", "image/svg+xml": ".svg",
        "video/mp4": ".mp4", "video/webm": ".webm",
        "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/ogg": ".ogg",
        "model/gltf+json": ".gltf", "model/gltf-binary": ".glb",
    }
    ext = ext_map.get(content_type, "")
    if not ext:
        from urllib.parse import urlparse
        ext = os.path.splitext(urlparse(url).path)[1].lower()
    if not ext:
        ext = ".bin"

    filename = f"ia_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    file_url = f"https://gestordecursos.pegui.edu.co:8000/static/resources/biblioteca/{filename}"

    ftype_str = FILE_TYPE_MAP.get(ext, data.file_type)
    try:
        ftype = ResourceType(ftype_str)
    except ValueError:
        ftype = ResourceType.image

    category = data.category or CATEGORY_MAP.get(ftype_str, "documentos")

    thumbnail = data.thumbnail_url
    if thumbnail and len(thumbnail) > 500:
        thumbnail = thumbnail[:500]

    resource = Resource(
        title=data.title,
        description=data.description or "",
        file_url=file_url,
        thumbnail_url=thumbnail,
        file_type=ftype,
        category=category,
        tags=data.tags or "",
        owner_id=token_data["user_id"],
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource

# 📌 Obtener recurso individual
@router.get("/{resource_id}", response_model=ResourceOut)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    res = db.query(Resource).filter(Resource.id == resource_id).first()
    if not res:
        raise HTTPException(404, "Recurso no encontrado")
    return res

