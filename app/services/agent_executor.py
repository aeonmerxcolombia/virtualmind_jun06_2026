import subprocess
import os
import json
from typing import Dict, Optional, Tuple

AGENT_CATEGORIES = {
    "backend": "tradicional",
    "frontend": "tradicional",
    "server": "tradicional",
    "database": "tradicional",
    "docs": "tradicional",
    "qa": "tradicional",
    "superadmin": "interfaz",
    "admin": "interfaz",
    "gerente-general": "interfaz",
    "autor": "interfaz",
    "coordinador": "interfaz",
    "cliente": "interfaz",
    "abogado": "interfaz",
    "revisor-qa": "interfaz",
    "ingeniero-lms": "interfaz",
    "editor": "interfaz",
    "guionista": "interfaz",
    "animador-2d": "interfaz",
    "animador-3d": "interfaz",
    "disenador-grafico": "interfaz",
    "disenador-instruccional": "interfaz",
    "desarrollador-multimedia": "interfaz",
    "corrector-de-estilo": "interfaz",
    "video": "interfaz",
    "registrado": "interfaz",
    "sistema_despachador_colmena": "sistema",
    "sistema_meta_factoria": "sistema",
    "sistema_self_play": "sistema",
    "sistema_linfocito": "sistema",
    "sistema_shadow_guardrail": "sistema",
    "sistema_insecto_planificador": "sistema",
    "sistema_consolidacion_sinaptica": "sistema",
    "sistema_adn_criptografico": "sistema",
    "sistema_hibernacion_sinaptica": "sistema",
    "sistema_finops": "sistema",
    "sistema_desarrollador_autosanador": "sistema",
    "sistema_perfilado_genetico": "sistema",
}

SKILL_MAP: Dict[str, str] = {
    "backend": "/home/william/skills/agents/backend.md",
    "frontend": "/home/william/skills/agents/frontend.md",
    "server": "/home/william/skills/agents/server.md",
    "database": "/home/william/skills/agents/database.md",
    "docs": "/home/william/skills/agents/docs.md",
    "qa": "/home/william/skills/agents/qa.md",
    "superadmin": "/home/william/skills/agents/rol_superadmin.md",
    "admin": "/home/william/skills/agents/rol_admin.md",
    "gerente-general": "/home/william/skills/agents/rol_gerente-general.md",
    "autor": "/home/william/skills/agents/rol_autor.md",
    "coordinador": "/home/william/skills/agents/rol_coordinador.md",
    "cliente": "/home/william/skills/agents/rol_cliente.md",
    "abogado": "/home/william/skills/agents/rol_abogado.md",
    "revisor-qa": "/home/william/skills/agents/rol_revisor-qa.md",
    "ingeniero-lms": "/home/william/skills/agents/rol_ingeniero-lms.md",
    "editor": "/home/william/skills/agents/rol_editor.md",
    "guionista": "/home/william/skills/agents/rol_guionista.md",
    "animador-2d": "/home/william/skills/agents/rol_animador-2d.md",
    "animador-3d": "/home/william/skills/agents/rol_animador-3d.md",
    "disenador-grafico": "/home/william/skills/agents/rol_disenador-grafico.md",
    "disenador-instruccional": "/home/william/skills/agents/rol_disenador-instruccional.md",
    "desarrollador-multimedia": "/home/william/skills/agents/rol_desarrollador-multimedia.md",
    "corrector-de-estilo": "/home/william/skills/agents/rol_corrector-de-estilo.md",
    "video": "/home/william/skills/agents/rol_video.md",
    "registrado": "/home/william/skills/agents/rol_registrado.md",
    "sistema_despachador_colmena": "/home/william/skills/agents/sys_despachador_colmena.md",
    "sistema_meta_factoria": "/home/william/skills/agents/sys_meta_factoria.md",
    "sistema_self_play": "/home/william/skills/agents/sys_self_play.md",
    "sistema_linfocito": "/home/william/skills/agents/sys_linfocito.md",
    "sistema_shadow_guardrail": "/home/william/skills/agents/sys_shadow_guardrail.md",
    "sistema_insecto_planificador": "/home/william/skills/agents/sys_insecto_planificador.md",
    "sistema_consolidacion_sinaptica": "/home/william/skills/agents/sys_consolidacion_sinaptica.md",
    "sistema_adn_criptografico": "/home/william/skills/agents/sys_adn_criptografico.md",
    "sistema_hibernacion_sinaptica": "/home/william/skills/agents/sys_hibernacion_sinaptica.md",
    "sistema_finops": "/home/william/skills/agents/sys_finops.md",
    "sistema_desarrollador_autosanador": "/home/william/skills/agents/sys_desarrollador_autosanador.md",
    "sistema_perfilado_genetico": "/home/william/skills/agents/sys_perfilado_genetico.md",
}

WORK_DIR_MAP: Dict[str, str] = {
    "backend": "/home/ubuntu/backend",
    "frontend": "/var/www/html",
    "server": "/etc",
    "database": "/home/ubuntu/backend",
    "docs": "/home/william/docs",
    "qa": "/home/ubuntu/backend",
    "superadmin": "/var/www/html",
    "admin": "/var/www/html",
    "gerente-general": "/var/www/html",
    "autor": "/var/www/html",
    "coordinador": "/var/www/html",
    "cliente": "/var/www/html",
    "abogado": "/var/www/html",
    "revisor-qa": "/var/www/html",
    "ingeniero-lms": "/var/www/html",
    "editor": "/var/www/html",
    "guionista": "/var/www/html",
    "animador-2d": "/var/www/html",
    "animador-3d": "/var/www/html",
    "disenador-grafico": "/var/www/html",
    "disenador-instruccional": "/var/www/html",
    "desarrollador-multimedia": "/var/www/html",
    "corrector-de-estilo": "/var/www/html",
    "video": "/var/www/html",
    "registrado": "/var/www/html",
    "sistema_despachador_colmena": "/home/ubuntu/backend",
    "sistema_meta_factoria": "/home/ubuntu/backend",
    "sistema_self_play": "/home/ubuntu/backend",
    "sistema_linfocito": "/home/ubuntu/backend",
    "sistema_shadow_guardrail": "/home/ubuntu/backend",
    "sistema_insecto_planificador": "/home/ubuntu/backend",
    "sistema_consolidacion_sinaptica": "/home/ubuntu/backend",
    "sistema_adn_criptografico": "/home/ubuntu/backend",
    "sistema_hibernacion_sinaptica": "/home/ubuntu/backend",
    "sistema_finops": "/home/ubuntu/backend",
    "sistema_desarrollador_autosanador": "/home/ubuntu/backend",
    "sistema_perfilado_genetico": "/home/ubuntu/backend",
}

OPENCODE_BIN = "/root/.opencode/bin/opencode"


class AgentExecutor:
    @staticmethod
    def get_category(agent_name: str) -> str:
        return AGENT_CATEGORIES.get(agent_name, "unknown")

    @staticmethod
    def get_skill_path(agent_name: str) -> str:
        return SKILL_MAP.get(agent_name, "")

    @staticmethod
    def get_work_dir(agent_name: str) -> str:
        return WORK_DIR_MAP.get(agent_name, "/home/ubuntu/backend")

    @staticmethod
    def load_skill(skill_path: str) -> str:
        if not skill_path:
            return ""
        try:
            with open(skill_path) as f:
                return f.read()
        except Exception:
            return ""

    @staticmethod
    def build_prompt(
        agent_name: str,
        task_description: str,
        category: str = None,
        skill_context: str = None,
        work_dir: str = None,
    ) -> str:
        if category is None:
            category = AgentExecutor.get_category(agent_name)
        if skill_context is None:
            skill_path = AgentExecutor.get_skill_path(agent_name)
            skill_context = AgentExecutor.load_skill(skill_path)
        if work_dir is None:
            work_dir = AgentExecutor.get_work_dir(agent_name)

        if category == "tradicional":
            skill_bloque = f"Tu skill de referencia:\n{skill_context}\n\n" if skill_context else ""
            return (
                f"Eres un agente especializado en: {agent_name}\n\n"
                f"{skill_bloque}"
                f"TAREA: {task_description}\n\n"
                "REGLAS:\n"
                f"1. Trabajas DENTRO de: {work_dir}\n"
                "2. Usa rutas RELATIVAS para no salirte de tu zona.\n"
                "3. No pidas permiso para usar herramientas comunes.\n"
                "4. Al terminar, confirma qué hiciste y cierra.\n"
                "5. Si algo falla, reporta el error claro."
            )

        elif category == "interfaz":
            skill_bloque = f"Tu perfil y permisos:\n{skill_context}\n\n" if skill_context else ""
            return (
                f"Eres un agente IA con rol: {agent_name} en VirtualMind.\n\n"
                f"{skill_bloque}"
                f"TAREA: {task_description}\n\n"
                "INSTRUCCIONES:\n"
                "1. Usa las APIs de VirtualMind via curl para hacer lo que tu rol permite.\n"
                "2. La API base es: https://gestordecursos.pegui.edu.co:8000\n"
                "3. Usa las rutas relativas de la interfaz si necesitas algo del frontend.\n"
                "4. Reporta claramente el resultado al final.\n"
                "5. Si necesitas token de acceso, puedes obtenerlo con login.\n"
                f"6. Trabajas dentro de: {work_dir}"
            )

        else:
            skill_bloque = f"Tu skill de sistema:\n{skill_context}\n\n" if skill_context else ""
            return (
                f"Eres un agente de sistema: {agent_name} en el Agentic OS VirtualMind.\n\n"
                f"{skill_bloque}"
                f"TAREA: {task_description}\n\n"
                "INSTRUCCIONES:\n"
                f"1. Trabajas dentro de: {work_dir}\n"
                "2. Ejecuta la tarea como agente de sistema interno.\n"
                "3. Reporta resultados usando rutas absolutas si creas archivos.\n"
                "4. Si algo falla, reporta el error con detalle para debugging.\n"
                "5. Al completar, confirma qué hiciste y el resultado final."
            )

    @staticmethod
    def run_opencode(
        prompt: str,
        work_dir: str,
        timeout: int = 150,
        log_file: str = None,
    ) -> Tuple[str, str]:
        proceso = subprocess.Popen(
            [OPENCODE_BIN, "run", "--pure", prompt],
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
        )

        try:
            stdout, stderr = proceso.communicate(input="Y\n", timeout=timeout)
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"===== STDOUT =====\n{stdout}\n")
                    if stderr:
                        f.write(f"===== STDERR =====\n{stderr}\n")
            return stdout, stderr
        except subprocess.TimeoutExpired:
            proceso.kill()
            stdout, stderr = proceso.communicate()
            if log_file:
                with open(log_file, "a") as f:
                    f.write(f"===== TIMEOUT ({timeout}s) =====\n{stdout}\n{stderr}\n")
            return stdout, stderr

    @classmethod
    def execute(
        cls,
        agent_name: str,
        task_description: str,
        task_id: int = None,
        work_dir: str = None,
        timeout: int = 150,
        log_prefix: str = "opencode",
    ) -> dict:
        category = cls.get_category(agent_name)
        if category == "unknown":
            return {"status": "error", "message": f"Agente desconocido: {agent_name}"}

        if work_dir is None:
            work_dir = cls.get_work_dir(agent_name)

        skill_path = cls.get_skill_path(agent_name)
        skill_context = cls.load_skill(skill_path)
        prompt = cls.build_prompt(agent_name, task_description, category, skill_context, work_dir)

        log_suffix = f"{task_id}" if task_id else f"{agent_name}_{id(prompt)}"
        log_file = f"/tmp/{log_prefix}_{log_suffix}.log"

        def log(msg):
            with open(log_file, "a") as f:
                f.write(f"{msg}\n")
            print(msg, flush=True)

        log(f"[*] Ejecutando agente: {agent_name} (categoria: {category})")
        log(f"[*] Directorio: {work_dir}")
        log(f"[*] Skill: {skill_path}")
        log(f"[*] Tarea: {task_description[:200]}")

        stdout, stderr = cls.run_opencode(prompt, work_dir, timeout, log_file)

        result = {
            "status": "completed" if stdout else "failed",
            "agent": agent_name,
            "category": category,
            "stdout": stdout[:5000] if stdout else "",
            "stderr": stderr[:2000] if stderr else "",
            "log_file": log_file,
        }

        log(f"[+] Agente {agent_name} finalizado. Status: {result['status']}")
        return result


executor = AgentExecutor()
