"""Columnas y tablas que llegaron sin migración en main (lider) + plantillas_proyecto

- colaboradores_proyecto: permiso_rol, puede_editar, puede_eliminar, puede_exportar, puede_usar_ia
  (CU38 del líder; antes solo se creaban en init_db, así que una base migrada solo con
  alembic fallaba en cualquier consulta de colaboradores).
- notifications / notifications_log: tokens FCM y bitácora de envíos del módulo
  gestion_notificaciones (app móvil).
- plantillas_proyecto (CU42): su migración e3f4a5b6c7d8 se quitó de la cadena en main;
  se vuelve a crear aquí con IF NOT EXISTS para que las bases nuevas la tengan.

Todo es idempotente: sirve igual en bases que ya tienen estas tablas por create_all/init_db.

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-11-10 00:00:00.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'b6c7d8e9f0a1'
down_revision = 'a5b6c7d8e9f0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    for sql in (
        "ALTER TABLE colaboradores_proyecto ADD COLUMN IF NOT EXISTS permiso_rol VARCHAR(20) NOT NULL DEFAULT 'editor'",
        "ALTER TABLE colaboradores_proyecto ADD COLUMN IF NOT EXISTS puede_editar BOOLEAN NOT NULL DEFAULT true",
        "ALTER TABLE colaboradores_proyecto ADD COLUMN IF NOT EXISTS puede_eliminar BOOLEAN NOT NULL DEFAULT true",
        "ALTER TABLE colaboradores_proyecto ADD COLUMN IF NOT EXISTS puede_exportar BOOLEAN NOT NULL DEFAULT true",
        "ALTER TABLE colaboradores_proyecto ADD COLUMN IF NOT EXISTS puede_usar_ia BOOLEAN NOT NULL DEFAULT true",
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id            SERIAL PRIMARY KEY,
            user_id       INTEGER NOT NULL,
            device_token  VARCHAR NOT NULL UNIQUE,
            created_at    TIMESTAMP WITHOUT TIME ZONE
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_notifications_id ON notifications (id)",
        "CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)",
        """
        CREATE TABLE IF NOT EXISTS notifications_log (
            id               SERIAL PRIMARY KEY,
            notification_id  INTEGER NOT NULL REFERENCES notifications (id),
            title            VARCHAR NOT NULL,
            body             TEXT NOT NULL,
            data             TEXT,
            sent             BOOLEAN,
            sent_at          TIMESTAMP WITHOUT TIME ZONE,
            priority         INTEGER,
            type             VARCHAR NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_notifications_log_id ON notifications_log (id)",
        """
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
        """,
        "CREATE INDEX IF NOT EXISTS ix_plantillas_proyecto_usuario_id ON plantillas_proyecto (usuario_id)",
    ):
        conn.execute(text(sql))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS plantillas_proyecto"))
    conn.execute(text("DROP TABLE IF EXISTS notifications_log"))
    conn.execute(text("DROP TABLE IF EXISTS notifications"))
    for col in ("puede_usar_ia", "puede_exportar", "puede_eliminar", "puede_editar", "permiso_rol"):
        conn.execute(text(f"ALTER TABLE colaboradores_proyecto DROP COLUMN IF EXISTS {col}"))
