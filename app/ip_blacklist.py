import os
import ipaddress

BLACKLIST_FILE = "/home/ubuntu/backend/ip_blacklist.txt"

def _load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return set()
    with open(BLACKLIST_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip() and not line.startswith("#"))

def _save_blacklist(ips):
    with open(BLACKLIST_FILE, "w") as f:
        f.write("# IPs bloqueadas - una por linea\n")
        for ip in sorted(ips):
            f.write(ip + "\n")

def is_ip_blocked(client_ip: str) -> bool:
    if not client_ip:
        return False
    blocked = _load_blacklist()
    if client_ip in blocked:
        return True
    for entry in blocked:
        try:
            if "/" in entry and ipaddress.ip_address(client_ip) in ipaddress.ip_network(entry, strict=False):
                return True
        except ValueError:
            pass
    return False

def add_ip_to_blacklist(ip: str):
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        try:
            ipaddress.ip_network(ip, strict=False)
        except ValueError:
            raise ValueError(f"IP o CIDR inválido: {ip}")
    blocked = _load_blacklist()
    blocked.add(ip)
    _save_blacklist(blocked)

def remove_ip_from_blacklist(ip: str):
    blocked = _load_blacklist()
    blocked.discard(ip)
    _save_blacklist(blocked)

def get_blacklist():
    return sorted(_load_blacklist())
