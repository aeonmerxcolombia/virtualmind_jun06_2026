#!/bin/bash
# opencode_agent.sh — Lanza un agente especializado opencode
# Uso: ./opencode_agent.sh <agente> <tarea>
#   agente: backend | frontend | server | database | docs | qa
#   tarea: descripción de la tarea a realizar

set -e

AGENT=$1
shift
TASK="$*"

if [ -z "$AGENT" ] || [ -z "$TASK" ]; then
    echo "Uso: $0 <agente> <tarea>"
    echo "Agentes: backend, frontend, server, database, docs, qa"
    exit 1
fi

SKILL_FILE="/home/william/skills/agents/${AGENT}.md"
SESSION_ID="ses_$(date +%s | md5sum | head -c 20)"

LOG_FILE="/tmp/opencode_agent_${AGENT}_${SESSION_ID}.log"

echo "[$(date)] Lanzando agente: $AGENT"
echo "[$(date)] Tarea: $TASK"
echo "[$(date)] Sesión: $SESSION_ID"
echo "[$(date)] Log: $LOG_FILE"

# Lanzar opencode run con la skill del agente como contexto
opencode run \
    --title "Agent: $AGENT - ${TASK:0:50}" \
    "Eres un agente especializado en $AGENT de VirtualMind.

Tu skill de referencia: file://$SKILL_FILE

TAREA: $TASK

Instrucciones:
1. Lee tu skill primero si es necesario
2. Completa la tarea
3. Verifica que funcione (prueba con curl si aplica)
4. Reporta el resultado final claramente" 2>&1 | tee "$LOG_FILE"

echo "[$(date)] Agente $AGENT completado. Log: $LOG_FILE"
