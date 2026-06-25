"""Create agentes_rol table

Revision ID: 002_agentes_rol
Revises: 001_initial
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = '002_agentes_rol'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS agentes_rol (
            id INT AUTO_INCREMENT PRIMARY KEY,
            rol VARCHAR(50) NOT NULL,
            descripcion TEXT NOT NULL,
            prioridad VARCHAR(20) DEFAULT 'medium',
            estado VARCHAR(20) DEFAULT 'pending',
            user_email VARCHAR(255) NULL,
            resultado TEXT NULL,
            notas TEXT NULL,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_rol (rol),
            INDEX idx_estado (estado)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agentes_rol")
