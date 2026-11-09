"""create versiones_contexto_ia (versión del diagrama antes/después de cada interacción de la IA)

Alimenta el preview de "versión anterior" del modal de memoria de la IA.
Idempotente (IF NOT EXISTS).

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-11-08 00:00:02.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS versiones_contexto_ia (
            id              BIGSERIAL NOT NULL,
            proyecto_id     INTEGER NOT NULL,
            ts              INTEGER NOT NULL,
            intent          VARCHAR NOT NULL,
            cmd             TEXT NOT NULL,
            resumen         TEXT NOT NULL,
            delta           VARCHAR NOT NULL,
            autor           VARCHAR,
            estado_antes    JSONB,
            estado_despues  JSONB,
            created_at      TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id) ON DELETE CASCADE
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_versiones_contexto_ia_proyecto ON versiones_contexto_ia (proyecto_id, id)"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS versiones_contexto_ia"))
