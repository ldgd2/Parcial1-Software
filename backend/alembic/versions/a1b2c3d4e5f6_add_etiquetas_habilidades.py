"""add etiquetas_habilidades to usuarios and create tareas_ia table

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-09-21 02:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Agregar columna solo si no existe ya
    conn.execute(text("""
        ALTER TABLE usuarios
        ADD COLUMN IF NOT EXISTS etiquetas_habilidades JSONB
    """))

    # Crear tabla tareas_ia solo si no existe ya
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS tareas_ia (
            id SERIAL PRIMARY KEY,
            proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
            usuario_id  INTEGER NOT NULL REFERENCES usuarios(id)  ON DELETE CASCADE,
            tipo        VARCHAR NOT NULL DEFAULT 'diagrama',
            titulo      VARCHAR NOT NULL,
            descripcion TEXT,
            completada  BOOLEAN NOT NULL DEFAULT false,
            orden       INTEGER NOT NULL DEFAULT 0
        )
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS tareas_ia"))
    conn.execute(text("ALTER TABLE usuarios DROP COLUMN IF EXISTS etiquetas_habilidades"))
