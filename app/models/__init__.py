# app/models/__init__.py
# Importar todos los modelos para que se registren en Base.metadata

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
from app.models.resource import Resource, ResourceType
from app.models.cronograma import Cronograma
from app.models.evaluacion import Evaluacion
from app.models.learning_activity import LearningActivity
from app.models.tarea_ia import TareaIA
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
from app.models.laboratorio_vr import LaboratorioVR, ModeloVR, ExperimentoVR, SesionVR
from app.models.biblioteca import DocumentoBiblioteca
from app.models.hoja_vida import HojaVida
from app.models.videocast import Videocast
