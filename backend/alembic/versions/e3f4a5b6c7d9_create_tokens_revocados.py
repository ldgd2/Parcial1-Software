"""create tokens_revocados (CU03: cerrar sesión invalida el token)

Revision ID: e3f4a5b6c7d9
Revises: a8b9c0d1e2f3
Create Date: 2026-11-10
"""
from alembic import op

revision = 'e3f4a5b6c7d9'
down_revision = 'a8b9c0d1e2f3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotente: init_db (create_all) puede haberla creado antes
    op.execute("""
        CREATE TABLE IF NOT EXISTS tokens_revocados (
            token_hash VARCHAR(64) PRIMARY KEY,
            expira_en TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tokens_revocados_expira_en ON tokens_revocados (expira_en)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tokens_revocados_expira_en")
    op.execute("DROP TABLE IF EXISTS tokens_revocados")
