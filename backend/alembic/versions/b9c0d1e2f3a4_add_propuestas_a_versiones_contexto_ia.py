"""propuestas de la IA con aprobación: payload, estado y quién decidió

La respuesta de la IA ya no se aplica sola: queda como propuesta 'pendiente'
hasta que alguien con permiso de edición la aprueba o la rechaza.
Idempotente (IF NOT EXISTS).

Revision ID: b9c0d1e2f3a4
Revises: a7b8c9d0e1f2
Create Date: 2026-11-08 00:00:03.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'b9c0d1e2f3a4'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    for sentencia in (
        "ALTER TABLE versiones_contexto_ia ADD COLUMN IF NOT EXISTS propuesta JSONB",
        "ALTER TABLE versiones_contexto_ia ADD COLUMN IF NOT EXISTS estado_propuesta VARCHAR",
        "ALTER TABLE versiones_contexto_ia ADD COLUMN IF NOT EXISTS decidida_por VARCHAR",
        "ALTER TABLE versiones_contexto_ia ADD COLUMN IF NOT EXISTS decidida_por_id INTEGER "
        "REFERENCES usuarios (id) ON DELETE SET NULL",
        "ALTER TABLE versiones_contexto_ia ADD COLUMN IF NOT EXISTS decidida_en TIMESTAMP WITH TIME ZONE",
    ):
        conn.execute(text(sentencia))


def downgrade() -> None:
    conn = op.get_bind()
    for col in ("decidida_en", "decidida_por_id", "decidida_por", "estado_propuesta", "propuesta"):
        conn.execute(text(f"ALTER TABLE versiones_contexto_ia DROP COLUMN IF EXISTS {col}"))
