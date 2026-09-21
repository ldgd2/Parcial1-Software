"""add etiquetas_habilidades to usuarios and create tareas_ia table

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-09-21 02:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar columna etiquetas_habilidades a la tabla usuarios
    op.add_column(
        'usuarios',
        sa.Column('etiquetas_habilidades', sa.JSON(), nullable=True)
    )

    # Crear tabla tareas_ia
    op.create_table(
        'tareas_ia',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('proyecto_id', sa.Integer(), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('usuario_id', sa.Integer(), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tipo', sa.String(), nullable=False, server_default='diagrama'),
        sa.Column('titulo', sa.String(), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('completada', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_table('tareas_ia')
    op.drop_column('usuarios', 'etiquetas_habilidades')
