"""Initial migration - create all tables (IF NOT EXISTS)

Revision ID: 001_initial
Revises: 
Create Date: 2026-03-25

NOTA: Esta migración usa CREATE TABLE IF NOT EXISTS para bases de datos existentes.
En una base de datos vacía funciona igual.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tablas con IF NOT EXISTS para MySQL
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) UNIQUE,
            description TEXT,
            created_at DATETIME
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE,
            description TEXT
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            uid VARCHAR(255) PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            tipo_documento VARCHAR(50) NOT NULL,
            documento VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            estado BOOLEAN DEFAULT TRUE,
            terms_accepted_at DATETIME
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_uid VARCHAR(255),
            foto_url VARCHAR(500),
            telefono VARCHAR(20),
            empresa VARCHAR(255),
            cargo VARCHAR(100),
            bio TEXT,
            linkedin VARCHAR(255),
            twitter VARCHAR(255),
            privacidad VARCHAR(20),
            FOREIGN KEY (user_uid) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            user_uid VARCHAR(255),
            role_id INT,
            FOREIGN KEY (user_uid) REFERENCES usuarios (uid),
            FOREIGN KEY (role_id) REFERENCES roles (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INT,
            permission_id INT,
            FOREIGN KEY (role_id) REFERENCES roles (id),
            FOREIGN KEY (permission_id) REFERENCES permissions (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS fases (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            descripcion TEXT,
            orden INT
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS etapas (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            fase_id BIGINT,
            descripcion TEXT,
            orden INT,
            FOREIGN KEY (fase_id) REFERENCES fases (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            fase_id BIGINT,
            name VARCHAR(255) NOT NULL,
            client_id VARCHAR(255) NOT NULL,
            codigo_referencia VARCHAR(100),
            start_date DATE NOT NULL,
            end_date DATE,
            tipo_proyecto VARCHAR(50),
            tipo_proyecto_personalizado VARCHAR(100),
            estado VARCHAR(50) DEFAULT 'Planificado',
            description TEXT,
            lenguaje_incluyente BOOLEAN DEFAULT FALSE,
            lenguaje_inclusivo_tipo VARCHAR(50),
            lenguaje_inclusivo_otro VARCHAR(100),
            inclusion_digital BOOLEAN DEFAULT FALSE,
            inclusion_digital_web BOOLEAN DEFAULT FALSE,
            inclusion_digital_asistiva BOOLEAN DEFAULT FALSE,
            inclusion_digital_universal BOOLEAN DEFAULT FALSE,
            inclusion_digital_educativa BOOLEAN DEFAULT FALSE,
            inclusion_digital_otro VARCHAR(100),
            idioma VARCHAR(100),
            idioma_otro VARCHAR(100),
            tipografia_titulo_fuente VARCHAR(100),
            tipografia_titulo_tamano VARCHAR(20),
            tipografia_titulo_negrita BOOLEAN DEFAULT FALSE,
            tipografia_titulo_cursiva BOOLEAN DEFAULT FALSE,
            tipografia_subtitulo_fuente VARCHAR(100),
            tipografia_subtitulo_tamano VARCHAR(20),
            tipografia_subtitulo_negrita BOOLEAN DEFAULT FALSE,
            tipografia_subtitulo_cursiva BOOLEAN DEFAULT FALSE,
            tipografia_parrafo_fuente VARCHAR(100),
            tipografia_parrafo_tamano VARCHAR(20),
            tipografia_parrafo_negrita BOOLEAN DEFAULT FALSE,
            tipografia_parrafo_cursiva BOOLEAN DEFAULT FALSE,
            horas_curso DECIMAL(7,2),
            diseno_grafico_tipo VARCHAR(50),
            diseno_grafico_paleta VARCHAR(120),
            cesion_derechos BOOLEAN DEFAULT FALSE,
            derechos_patrimoniales_autor BOOLEAN DEFAULT FALSE,
            acuerdo_confidencialidad BOOLEAN DEFAULT FALSE,
            entrega_fuentes BOOLEAN DEFAULT FALSE,
            entrega_escrito_autor BOOLEAN DEFAULT FALSE,
            entrega_diseno_instruccional BOOLEAN DEFAULT FALSE,
            publico_objetivo TEXT,
            publico_objetivo_otro VARCHAR(255),
            horas_aprendizaje_autonomo_virtual DECIMAL(7,2),
            horas_actividades_aprendizaje DECIMAL(7,2),
            observaciones TEXT,
            ultima_actualizacion DATETIME,
            etapa VARCHAR(255),
            FOREIGN KEY (client_id) REFERENCES usuarios (uid),
            FOREIGN KEY (fase_id) REFERENCES fases (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            descripcion TEXT,
            proyecto_id BIGINT,
            asignado_a VARCHAR(255),
            estado VARCHAR(50),
            prioridad VARCHAR(20),
            fecha_limite DATE,
            fecha_inicio DATE,
            fecha_fin DATE,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY (proyecto_id) REFERENCES projects (id),
            FOREIGN KEY (asignado_a) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            descripcion TEXT,
            curso_id BIGINT,
            orden INT,
            created_at DATETIME,
            FOREIGN KEY (curso_id) REFERENCES projects (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS units (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            contenido TEXT,
            modulo_id BIGINT,
            orden INT,
            created_at DATETIME,
            FOREIGN KEY (modulo_id) REFERENCES modules (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS learning_activities (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            tipo VARCHAR(50),
            contenido TEXT,
            unidad_id BIGINT,
            created_at DATETIME,
            FOREIGN KEY (unidad_id) REFERENCES units (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            tipo VARCHAR(50),
            ruta VARCHAR(500),
            propietario_id VARCHAR(255),
            proyecto_id BIGINT,
            created_at DATETIME,
            FOREIGN KEY (propietario_id) REFERENCES usuarios (uid),
            FOREIGN KEY (proyecto_id) REFERENCES projects (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS archivos (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            ruta VARCHAR(500) NOT NULL,
            tipo VARCHAR(50),
            tamano BIGINT,
            uploader_id VARCHAR(255),
            proyecto_id BIGINT,
            created_at DATETIME,
            FOREIGN KEY (uploader_id) REFERENCES usuarios (uid),
            FOREIGN KEY (proyecto_id) REFERENCES projects (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            ruta VARCHAR(500),
            parent_id BIGINT,
            owner_id VARCHAR(255),
            created_at DATETIME,
            FOREIGN KEY (owner_id) REFERENCES usuarios (uid),
            FOREIGN KEY (parent_id) REFERENCES folders (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS competencias (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            descripcion TEXT,
            created_at DATETIME
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS study_plans (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            descripcion TEXT,
            modulo_id BIGINT,
            usuario_id VARCHAR(255),
            created_at DATETIME,
            FOREIGN KEY (modulo_id) REFERENCES modules (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            descripcion TEXT,
            unidad_id BIGINT,
            tipo VARCHAR(50),
            created_at DATETIME,
            FOREIGN KEY (unidad_id) REFERENCES units (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS evaluaciones (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            descripcion TEXT,
            unidad_id BIGINT,
            tipo VARCHAR(50),
            created_at DATETIME,
            FOREIGN KEY (unidad_id) REFERENCES units (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS notificaciones (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            usuario_id VARCHAR(255),
            titulo VARCHAR(255) NOT NULL,
            descripcion TEXT,
            leida BOOLEAN DEFAULT FALSE,
            tipo VARCHAR(50),
            fecha DATETIME,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            usuario_id VARCHAR(255),
            accion VARCHAR(100) NOT NULL,
            tabla_afectada VARCHAR(50),
            registro_id BIGINT,
            ip VARCHAR(45),
            fecha DATETIME,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS logs_acciones (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            usuario_id VARCHAR(255),
            accion VARCHAR(255) NOT NULL,
            detalles TEXT,
            fecha DATETIME,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            remitente_id VARCHAR(255),
            destinatario_id VARCHAR(255),
            asunto VARCHAR(255),
            contenido TEXT,
            leido BOOLEAN DEFAULT FALSE,
            fecha DATETIME,
            FOREIGN KEY (remitente_id) REFERENCES usuarios (uid),
            FOREIGN KEY (destinatario_id) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS podcasts (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            descripcion TEXT,
            audio_url VARCHAR(500),
            duracion INT,
            usuario_id VARCHAR(255),
            created_at DATETIME,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            tipo VARCHAR(50),
            url VARCHAR(500),
            descripcion TEXT,
            owner_id VARCHAR(255),
            created_at DATETIME,
            FOREIGN KEY (owner_id) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS cronogramas (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            proyecto_id BIGINT,
            contenido TEXT,
            created_at DATETIME,
            FOREIGN KEY (proyecto_id) REFERENCES projects (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS tareas_ia (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            descripcion TEXT,
            responsable VARCHAR(50),
            estado VARCHAR(50),
            prioridad VARCHAR(20),
            fecha_creacion DATETIME,
            fecha_actualizacion DATETIME
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS client_profiles (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_uid VARCHAR(255),
            empresa VARCHAR(255),
            cargo VARCHAR(100),
            telefono VARCHAR(20),
            direccion TEXT,
            created_at DATETIME,
            FOREIGN KEY (user_uid) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS client_documents (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_uid VARCHAR(255),
            tipo VARCHAR(50),
            nombre VARCHAR(255) NOT NULL,
            ruta VARCHAR(500),
            fecha_subida DATETIME,
            FOREIGN KEY (user_uid) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS author_content_forms (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            proyecto_id BIGINT,
            contenido JSON,
            created_at DATETIME,
            FOREIGN KEY (proyecto_id) REFERENCES projects (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS instructional_design_forms (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            proyecto_id BIGINT,
            contenido JSON,
            created_at DATETIME,
            FOREIGN KEY (proyecto_id) REFERENCES projects (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS contacto_mensajes (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            asunto VARCHAR(255),
            mensaje TEXT NOT NULL,
            fecha DATETIME
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            clave VARCHAR(100) NOT NULL UNIQUE,
            valor TEXT,
            descripcion TEXT
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            study_plan_id BIGINT NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            author VARCHAR(100),
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY (study_plan_id) REFERENCES study_plans (id)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INT AUTO_INCREMENT PRIMARY KEY,
            accion VARCHAR(255),
            entidad VARCHAR(50),
            referencia_id VARCHAR(255),
            usuario_uid VARCHAR(255),
            fecha DATETIME,
            FOREIGN KEY (usuario_uid) REFERENCES usuarios (uid)
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            token VARCHAR(255) NOT NULL UNIQUE,
            created_at DATETIME,
            code VARCHAR(10),
            expires_at DATETIME,
            used BOOLEAN DEFAULT FALSE
        )
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_participants (
            project_id INT NOT NULL,
            user_uid VARCHAR(255) NOT NULL,
            PRIMARY KEY (project_id, user_uid),
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (user_uid) REFERENCES usuarios (uid)
        )
    """)


def downgrade() -> None:
    # No hacer downgrade en producción
    pass
