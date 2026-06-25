#!/bin/bash
# Auto-healing script - verifica servicios críticos y los revive si están caídos
# Ejecutado por systemd timer cada 5 minutos

SERVICES=("virtualmind" "mcp-gemini" "mcp-ollama" "ollama")
LOG="/var/log/auto-heal.log"

for svc in "${SERVICES[@]}"; do
    STATUS=$(systemctl is-active "$svc" 2>/dev/null)
    if [ "$STATUS" != "active" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $svc está $STATUS — intentando reiniciar..." >> "$LOG"
        systemctl restart "$svc" 2>/dev/null
        sleep 2
        NEW_STATUS=$(systemctl is-active "$svc" 2>/dev/null)
        if [ "$NEW_STATUS" = "active" ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $svc reiniciado exitosamente" >> "$LOG"
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $svc NO pudo reiniciarse (ahora: $NEW_STATUS)" >> "$LOG"
        fi
    fi
done

# También verificar MySQL
if ! systemctl is-active --quiet mysql 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  mysql está caído — intentando reiniciar..." >> "$LOG"
    systemctl restart mysql 2>/dev/null
fi

# Verificar Apache
if ! systemctl is-active --quiet apache2 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  apache2 está caído — intentando reiniciar..." >> "$LOG"
    systemctl restart apache2 2>/dev/null
fi
