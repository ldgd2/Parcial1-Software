"""Preferencias de notificación por usuario (módulo móvil del líder, ahora en gestion_notificaciones)

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-11-10 00:00:01.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'c7d8e9f0a1b2'
down_revision = 'b6c7d8e9f0a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id                        SERIAL PRIMARY KEY,
            user_id                   INTEGER NOT NULL,
            receive_position_updates  BOOLEAN,
            receive_semantic_changes  BOOLEAN,
            receive_comments          BOOLEAN,
            receive_invitations       BOOLEAN,
            receive_task_assignments  BOOLEAN,
            quiet_mode                BOOLEAN,
            quiet_mode_until          TIMESTAMP WITHOUT TIME ZONE,
            created_at                TIMESTAMP WITHOUT TIME ZONE
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_preferences_id ON notification_preferences (id)"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_notification_preferences_user_id ON notification_preferences (user_id)"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS notification_preferences"))
