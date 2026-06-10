from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.auth.jwt_handler import verify_token
from app.ip_blacklist import add_ip_to_blacklist, remove_ip_from_blacklist, get_blacklist

router = APIRouter(prefix="/ip-blacklist", tags=["IP Blacklist"])

class IPEntry(BaseModel):
    ip: str

@router.get("/")
def list_blacklist(token_data: dict = Depends(verify_token)):
    roles = token_data.get("roles", [])
    if "superadmin" not in roles:
        raise HTTPException(status_code=403, detail="Solo superadmin")
    return {"blocked_ips": get_blacklist()}

@router.post("/")
def block_ip(entry: IPEntry, token_data: dict = Depends(verify_token)):
    roles = token_data.get("roles", [])
    if "superadmin" not in roles:
        raise HTTPException(status_code=403, detail="Solo superadmin")
    try:
        add_ip_to_blacklist(entry.ip)
        return {"message": f"IP {entry.ip} bloqueada"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/")
def unblock_ip(entry: IPEntry, token_data: dict = Depends(verify_token)):
    roles = token_data.get("roles", [])
    if "superadmin" not in roles:
        raise HTTPException(status_code=403, detail="Solo superadmin")
    remove_ip_from_blacklist(entry.ip)
    return {"message": f"IP {entry.ip} desbloqueada"}
