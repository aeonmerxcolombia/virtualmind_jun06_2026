from typing import List


class EnswarmConfig:
    JWT_SECRET: str = "YOUR_JWT_SECRET_HERE"
    ALGORITHM: str = "HS256"
    OLLAMA_URL: str = "http://localhost:11434/api/generate"
    DATABASE_URL: str = (
        "mysql+aiomysql://root:YOUR_DB_PASSWORD@localhost:3306/agentic_os"
    )
    CODE_SIGN_KEY: str = "YOUR_CODE_SIGN_KEY_HERE"
    SQLITE_DB_PATH: str = "/tmp/agentic_os_hibernation.db"

    # Pool de API Keys — reemplazar con tus propias keys
    GEMINI_API_KEYS: List[str] = [
        "YOUR_GEMINI_KEY_1",
        "YOUR_GEMINI_KEY_2",
        "YOUR_GEMINI_KEY_3",
        "YOUR_GEMINI_KEY_4",
        "YOUR_GEMINI_KEY_5",
    ]

    # Modelos Google (nada de 1.5)
    MODEL_FAST: str = "gemini-2.5-flash"
    MODEL_COMPLEX: str = "gemini-3.5-flash"
    MODEL_EMBEDDING: str = "gemini-embedding-2"

    ROLES_INTERFAZ: List[str] = [
        "abogado",
        "admin",
        "animador-2d",
        "animador-3d",
        "autor",
        "cliente",
        "coordinador",
        "corrector-de-estilo",
        "desarrollador-multimedia",
        "disenador-grafico",
        "disenador-instruccional",
        "editor",
        "gerente-general",
        "guionista",
        "ingeniero-lms",
        "registrado",
        "revisor-qa",
        "superadmin",
        "video",
    ]

    ROLES_SISTEMA: List[str] = [
        "despachador_colmena",
        "meta_factoria",
        "self_play",
        "linfocito",
        "shadow_guardrail",
        "insecto_planificador",
        "consolidacion_sinaptica",
        "adn_criptografico",
        "hibernacion_sinaptica",
        "finops",
        "desarrollador_autosanador",
        "perfilado_genetico",
    ]


settings = EnswarmConfig()
