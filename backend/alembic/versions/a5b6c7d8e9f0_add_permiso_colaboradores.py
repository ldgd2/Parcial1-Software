"""CU38: permiso persistente por colaborador (edit | view)

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-11-09 00:00:04.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'a5b6c7d8e9f0'
down_revision = 'f4a5b6c7d8e9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text(
        "ALTER TABLE colaboradores_proyecto ADD COLUMN IF NOT EXISTS permiso VARCHAR(10) DEFAULT 'edit' NOT NULL"
    ))
    conn.execute(text("ALTER TABLE colaboradores_proyecto ALTER COLUMN permiso SET DEFAULT 'edit'"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE colaboradores_proyecto DROP COLUMN IF EXISTS permiso"))
