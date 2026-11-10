"""CU39: tabla user_notification_preferences (definida en el modelo pero sin migración)

Revision ID: a8b9c0d1e2f3
Revises: f4a5b6c7d8e9
Create Date: 2026-11-10 00:00:00.000000

"""
from alembic import op
from sqlalchemy import text

revision = 'a8b9c0d1e2f3'
down_revision = 'f4a5b6c7d8e9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS user_notification_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            receive_position_updates BOOLEAN NOT NULL DEFAULT false,
            receive_semantic_changes BOOLEAN NOT NULL DEFAULT true,
            receive_comments BOOLEAN NOT NULL DEFAULT false,
            receive_invitations BOOLEAN NOT NULL DEFAULT true,
            receive_task_assignments BOOLEAN NOT NULL DEFAULT true,
            quiet_mode BOOLEAN NOT NULL DEFAULT false,
            quiet_mode_until TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_notification_preferences_user_id ON user_notification_preferences (user_id)"))


def downgrade() -> None:
    op.get_bind().execute(text("DROP TABLE IF EXISTS user_notification_preferences"))
