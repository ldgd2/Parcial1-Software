"""add rol_ia, areas, responsabilidades to colaboradores_proyecto and area to tareas_ia

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-07 08:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(text("""
        ALTER TABLE colaboradores_proyecto
        ADD COLUMN IF NOT EXISTS rol_ia VARCHAR
    """))

    conn.execute(text("""
        ALTER TABLE colaboradores_proyecto
        ADD COLUMN IF NOT EXISTS areas JSONB
    """))

    conn.execute(text("""
        ALTER TABLE colaboradores_proyecto
        ADD COLUMN IF NOT EXISTS responsabilidades JSONB
    """))

    conn.execute(text("""
        ALTER TABLE tareas_ia
        ADD COLUMN IF NOT EXISTS area VARCHAR DEFAULT 'general'
    """))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(text("""
        ALTER TABLE colaboradores_proyecto DROP COLUMN IF EXISTS rol_ia
    """))

    conn.execute(text("""
        ALTER TABLE colaboradores_proyecto DROP COLUMN IF EXISTS areas
    """))

    conn.execute(text("""
        ALTER TABLE colaboradores_proyecto DROP COLUMN IF EXISTS responsabilidades
    """))

    conn.execute(text("""
        ALTER TABLE tareas_ia DROP COLUMN IF EXISTS area
    """))

