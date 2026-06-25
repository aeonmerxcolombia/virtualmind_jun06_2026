import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
import subprocess
import os
import datetime
import httpx
import json
from app.auth.jwt_handler import verify_token

router = APIRouter(prefix="/diagnostico", tags=["diagnostico"])

SERVICES = ["virtualmind", "mcp-gemini", "mcp-ollama", "ollama"]

async def check_mcp_health(url: str, name: str):
    try:
        async with httpx.AsyncClient(verify=False, timeout=5) as c:
            r = await c.get(f"{url}/health")
            if r.status_code == 200:
                data = r.json()
                return {"name": name, "status": "ok", "detail": data}
            return {"name": name, "status": "error", "detail": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"name": name, "status": "error", "detail": str(e)[:200]}

def check_service(name: str):
    try:
        r = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=5
        )
        status = r.stdout.strip()
        return {"name": name, "status": status}
    except:
        return {"name": name, "status": "unknown"}

def check_disk():
    try:
        r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        lines = r.stdout.strip().split("\n")
        parts = lines[1].split()
        return {
            "filesystem": parts[0],
            "size": parts[1],
            "used": parts[2],
            "available": parts[3],
            "use_percent": parts[4]
        }
    except:
        return {"error": "N/A"}

def check_ssl():
    try:
        r = subprocess.run(
            ["openssl", "x509", "-enddate", "-noout",
             "-in", "/etc/letsencrypt/live/gestordecursos.pegui.edu.co/fullchain.pem"],
            capture_output=True, text=True, timeout=5
        )
        end_date_str = r.stdout.strip().replace("notAfter=", "")
        end_date = datetime.datetime.strptime(end_date_str, "%b %d %H:%M:%S %Y %Z")
        now = datetime.datetime.now()
        days_left = (end_date - now).days
        return {
            "expires": end_date_str,
            "days_left": days_left,
            "expired": days_left < 0,
            "critical": days_left < 30
        }
    except:
        return {"error": "N/A"}

def check_docker():
    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"],
            capture_output=True, text=True, timeout=5
        )
        containers = []
        for line in r.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) >= 2:
                containers.append({
                    "name": parts[0],
                    "status": parts[1],
                    "ports": parts[2] if len(parts) > 2 else ""
                })
        return containers
    except:
        return [{"error": "Docker no disponible"}]

def check_cpu():
    try:
        r = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
        uptime_str = r.stdout.strip()
        r2 = subprocess.run(["nproc"], capture_output=True, text=True, timeout=5)
        cpus = r2.stdout.strip()
        r3 = subprocess.run(["cat", "/proc/loadavg"], capture_output=True, text=True, timeout=5)
        load = r3.stdout.strip().split()[:3]
        return {
            "uptime": uptime_str,
            "cpus": cpus,
            "load_1min": load[0] if load else "N/A",
            "load_5min": load[1] if len(load) > 1 else "N/A",
            "load_15min": load[2] if len(load) > 2 else "N/A"
        }
    except:
        return {"error": "N/A"}

def check_memory():
    try:
        r = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5)
        lines = r.stdout.strip().split("\n")
        parts = lines[1].split()
        return {
            "total_mb": int(parts[1]),
            "used_mb": int(parts[2]),
            "free_mb": int(parts[3]),
            "available_mb": int(parts[6]),
            "used_percent": round(int(parts[2]) / int(parts[1]) * 100, 1) if int(parts[1]) > 0 else 0
        }
    except:
        return {"error": "N/A"}

def check_swap():
    try:
        r = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5)
        lines = r.stdout.strip().split("\n")
        parts = lines[2].split()
        total = int(parts[1])
        if total == 0:
            return {"total_mb": 0, "used_mb": 0, "free_mb": 0}
        return {
            "total_mb": total,
            "used_mb": int(parts[2]),
            "free_mb": int(parts[3])
        }
    except:
        return {"error": "N/A"}

def get_recent_errors():
    try:
        r = subprocess.run(
            ["journalctl", "-u", "virtualmind", "--no-pager", "-n", "10", "--priority", "err"],
            capture_output=True, text=True, timeout=5
        )
        errors = [l for l in r.stdout.strip().split("\n") if l.strip()]
        return errors[:5]
    except:
        return []

def check_network():
    try:
        r = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5)
        ips = r.stdout.strip().split()
        return {"ips": ips}
    except:
        return {"error": "N/A"}

@router.get("/")
async def get_diagnostico(token_data: dict = Depends(verify_token)):
    roles = token_data.get("roles", [])
    if "superadmin" not in roles:
        raise HTTPException(status_code=403, detail="Solo superadmin puede ver diagnóstico")

    services = [check_service(s) for s in SERVICES]
    memory = check_memory()
    swap = check_swap()
    disk = check_disk()
    ssl = check_ssl()
    cpu = check_cpu()
    docker = check_docker()
    network = check_network()
    errors = get_recent_errors()

    mcp_checks = await asyncio.gather(
        check_mcp_health("https://127.0.0.1:8001", "MCP Gemini"),
        check_mcp_health("https://127.0.0.1:8002", "MCP Ollama"),
        return_exceptions=True
    )

    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "servicios": services,
        "mcp": [m for m in mcp_checks if not isinstance(m, Exception)],
        "cpu": cpu,
        "memoria": memory,
        "swap": swap,
        "disco": disk,
        "ssl": ssl,
        "docker": docker,
        "red": network,
        "errores_recientes": errors
    }

@router.post("/heal")
async def heal_service(
    service: str = Query(..., description="Nombre del servicio a revivir"),
    token_data: dict = Depends(verify_token)
):
    roles = token_data.get("roles", [])
    if "superadmin" not in roles:
        raise HTTPException(status_code=403, detail="Solo superadmin puede ejecutar auto-healing")

    valid_services = ["virtualmind", "mcp-gemini", "mcp-ollama", "ollama", "apache2", "mysql"]
    if service not in valid_services:
        raise HTTPException(status_code=400, detail=f"Servicio no válido. Válidos: {', '.join(valid_services)}")

    try:
        r = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True, timeout=5)
        current = r.stdout.strip()
        if current == "active":
            return {"service": service, "action": "skipped", "reason": "Ya está activo", "previous_state": current}

        r2 = subprocess.run(
            ["sudo", "systemctl", "restart", service],
            capture_output=True, text=True, timeout=30
        )
        r3 = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True, timeout=5)
        new_state = r3.stdout.strip()

        return {
            "service": service,
            "action": "restarted" if new_state == "active" else "failed",
            "previous_state": current,
            "current_state": new_state,
            "output": r2.stdout.strip()[:500] or r2.stderr.strip()[:500]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
