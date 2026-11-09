"""memoria del proyecto estilo Engram: observaciones con tema, búsqueda en español y conflictos

Revision ID: c1d2e3f4a5b6
Revises: b9c0d1e2f3a4
Create Date: 2026-11-09 00:00:00.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'b9c0d1e2f3a4'
branch_labels = None
depends_on = None

BUSQUEDA = (
    "to_tsvector('spanish', coalesce(topic_key, '') || ' ' || coalesce(titulo, '') || ' ' || "
    "coalesce(que, '') || ' ' || coalesce(por_que, '') || ' ' || coalesce(donde, '') || ' ' || "
    "coalesce(aprendido, ''))"
)


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS memorias_ia (
            id            BIGSERIAL NOT NULL,
            proyecto_id   INTEGER NOT NULL,
            tipo          VARCHAR NOT NULL,
            topic_key     VARCHAR NOT NULL,
            titulo        VARCHAR NOT NULL,
            que           TEXT NOT NULL,
            por_que       TEXT NOT NULL,
            donde         TEXT NOT NULL,
            aprendido     TEXT NOT NULL,
            origen        VARCHAR NOT NULL,
            version_id    BIGINT,
            autor         VARCHAR,
            vigente       BOOLEAN DEFAULT true NOT NULL,
            reemplaza_id  BIGINT,
            en_conflicto  BOOLEAN DEFAULT false NOT NULL,
            busqueda      TSVECTOR GENERATED ALWAYS AS ({BUSQUEDA}) STORED,
            created_at    TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at    TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id) ON DELETE CASCADE,
            FOREIGN KEY (version_id) REFERENCES versiones_contexto_ia (id) ON DELETE SET NULL,
            FOREIGN KEY (reemplaza_id) REFERENCES memorias_ia (id) ON DELETE SET NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_memorias_ia_proyecto ON memorias_ia (proyecto_id, vigente)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_memorias_ia_busqueda ON memorias_ia USING gin (busqueda)"))
    conn.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_memorias_ia_tema_vigente ON memorias_ia (proyecto_id, topic_key) WHERE vigente"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS memorias_ia"))
