"""CU39: notificaciones y dispositivos push (Firebase)

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-11-09 00:00:03.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'f4a5b6c7d8e9'
down_revision = 'd2e3f4a5b6c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notificaciones (
            id           BIGSERIAL NOT NULL,
            usuario_id   INTEGER NOT NULL,
            proyecto_id  INTEGER,
            tipo         VARCHAR(40) NOT NULL,
            titulo       VARCHAR(160) NOT NULL,
            mensaje      TEXT DEFAULT '' NOT NULL,
            url          VARCHAR(300),
            leida        BOOLEAN DEFAULT false NOT NULL,
            created_at   TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id) ON DELETE CASCADE
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_notificaciones_usuario_leida "
        "ON notificaciones (usuario_id, leida, created_at)"
    ))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS dispositivos_push (
            id           BIGSERIAL NOT NULL,
            usuario_id   INTEGER NOT NULL,
            token        VARCHAR(512) NOT NULL,
            plataforma   VARCHAR(20) DEFAULT 'web' NOT NULL,
            created_at   TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            PRIMARY KEY (id),
            UNIQUE (token),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_dispositivos_push_usuario_id ON dispositivos_push (usuario_id)"))
    # Si el backend ya las creó con create_all, asegurar los valores por defecto en la base
    conn.execute(text("ALTER TABLE notificaciones ALTER COLUMN leida SET DEFAULT false"))
    conn.execute(text("ALTER TABLE notificaciones ALTER COLUMN mensaje SET DEFAULT ''"))
    conn.execute(text("ALTER TABLE dispositivos_push ALTER COLUMN plataforma SET DEFAULT 'web'"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS dispositivos_push"))
    conn.execute(text("DROP TABLE IF EXISTS notificaciones"))
