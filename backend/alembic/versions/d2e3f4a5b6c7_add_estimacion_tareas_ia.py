"""CU37: estimación de esfuerzo en tareas_ia (horas y complejidad)

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-11-09 00:00:01.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'd2e3f4a5b6c7'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE tareas_ia ADD COLUMN IF NOT EXISTS estimacion_horas INTEGER"))
    conn.execute(text("ALTER TABLE tareas_ia ADD COLUMN IF NOT EXISTS complejidad VARCHAR"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE tareas_ia DROP COLUMN IF EXISTS complejidad"))
    conn.execute(text("ALTER TABLE tareas_ia DROP COLUMN IF EXISTS estimacion_horas"))
