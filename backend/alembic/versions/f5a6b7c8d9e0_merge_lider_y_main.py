"""Une las dos ramas de migraciones que salieron de f4a5b6c7d8e9 (lider y main)

- main:  a5b6c7d8e9f0 (permiso) -> b6c7d8e9f0a1 -> c7d8e9f0a1b2 (notification_preferences)
- lider: a8b9c0d1e2f3 -> e3f4a5b6c7d9 (tokens_revocados)

Además deja un solo permiso válido por colaborador. Las dos ramas guardaban el rol Lector en
columnas distintas: `permiso` ('edit' | 'view') y `permiso_rol` ('editor' | 'lector') + `puede_*`.
La fuente de verdad pasa a ser `permiso`; las columnas viejas se copian de ella.

Revision ID: f5a6b7c8d9e0
Revises: c7d8e9f0a1b2, e3f4a5b6c7d9
Create Date: 2026-11-10
"""
from alembic import op

revision = 'f5a6b7c8d9e0'
down_revision = ('c7d8e9f0a1b2', 'e3f4a5b6c7d9')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Quien quedó como Lector por la rama lider (permiso_rol / puede_editar) también lo es en `permiso`
    op.execute("""
        UPDATE colaboradores_proyecto
           SET permiso = 'view'
         WHERE rol_proyecto <> 'anfitrion'
           AND (permiso_rol = 'lector' OR puede_editar = false)
    """)
    # Y al revés: las columnas viejas reflejan `permiso`
    op.execute("""
        UPDATE colaboradores_proyecto
           SET permiso_rol    = CASE WHEN permiso = 'view' THEN 'lector' ELSE 'editor' END,
               puede_editar   = (permiso <> 'view'),
               puede_eliminar = (permiso <> 'view'),
               puede_usar_ia  = (permiso <> 'view')
         WHERE rol_proyecto <> 'anfitrion'
    """)


def downgrade() -> None:
    pass  # solo une ramas y sincroniza datos
