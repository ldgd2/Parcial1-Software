"""fix usuarios.tipo: 'registrado' -> 'usuarioregistrado'

El launcher (Usuarios > Crear Usuario) y el DEFAULT de la columna guardaban
tipo = 'registrado', que no es una identidad polimórfica válida. Las válidas son
las que genera `heredar()` en gestion_usuarios/models.py:
'usuario', 'usuarioregistrado' y 'usuarioanonimo'.
Con 'registrado', SQLAlchemy no puede leer la fila
("No such polymorphic_identity 'registrado' is defined").

Revision ID: f1a2b3c4d5e6
Revises: e9f0a1b2c3d4
Create Date: 2026-11-08 00:00:01.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e9f0a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("UPDATE usuarios SET tipo = 'usuarioregistrado' WHERE tipo = 'registrado'"))
    conn.execute(text("ALTER TABLE usuarios ALTER COLUMN tipo SET DEFAULT 'usuarioregistrado'"))


def downgrade() -> None:
    # Solo se revierte el DEFAULT; volver las filas a 'registrado' las dejaría ilegibles otra vez.
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE usuarios ALTER COLUMN tipo SET DEFAULT 'registrado'"))
