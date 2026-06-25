from logging.config import fileConfig
import sys
import os

# Agregar el path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Forzar importación de todos los modelos
from app.database.db import Base
from app.models.user import User, user_roles
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.models.profile import Profile
from app.models.project import Project
from app.models.tarea import Tarea
from app.models.module import Module
from app.models.unit import Unit
from app.models.fase import Fase
from app.models.etapa import Etapa
from app.models.document import Document
from app.models.archivo import Archivo
from app.models.competencia import Competencia
from app.models.study_plan import StudyPlan
from app.models.podcast import Podcast
from app.models.resource import Resource
from app.models.cronograma import Cronograma
from app.models.evaluacion import Evaluacion
from app.models.learning_activity import LearningActivity
from app.models.tarea_ia import TareaIA
from app.models.agente_rol import AgenteRol
from app.models.client_profile import ClientProfile
from app.models.client_document import ClientDocument
from app.models.folder import Folder
from app.models.mensaje import Mensaje
from app.models.log_model import LogAccion
from app.models.solicitud import SolicitudPieza
from app.models.audit_log import AuditLog
from app.models.author_content_form import AuthorContentForm
from app.models.instructional_design_form import InstructionalDesignForm
from app.models.contact_model import ContactMessage, Configuracion

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Target metadata para autogenerate
target_metadata = Base.metadata

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# target_metadata ya definido arriba

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
