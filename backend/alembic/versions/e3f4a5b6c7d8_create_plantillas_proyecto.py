"""CU42: plantillas de proyecto guardadas por los usuarios

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-11-09 00:00:02.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'e3f4a5b6c7d8'
down_revision = 'd2e3f4a5b6c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS plantillas_proyecto (
            id           BIGSERIAL NOT NULL,
            usuario_id   INTEGER NOT NULL,
            nombre       VARCHAR NOT NULL,
            descripcion  TEXT NOT NULL,
            lienzo       JSONB NOT NULL,
            created_at   TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_plantillas_proyecto_usuario_id ON plantillas_proyecto (usuario_id)"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS plantillas_proyecto"))
