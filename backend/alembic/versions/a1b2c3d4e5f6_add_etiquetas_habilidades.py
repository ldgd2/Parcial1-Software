"""add etiquetas_habilidades to usuarios and create tareas_ia table

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-09-21 02:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Esta es la migración inicial del repositorio y las migraciones anteriores
    # fueron eliminadas. Crear el esquema base permite ejecutarla en una BD vacía.
    base_tables = (
        """
        CREATE TABLE IF NOT EXISTS permisos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR NOT NULL UNIQUE,
            descripcion VARCHAR
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS roles (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR NOT NULL UNIQUE,
            descripcion VARCHAR
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS roles_permisos (
            rol_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            permiso_id INTEGER NOT NULL REFERENCES permisos(id) ON DELETE CASCADE,
            PRIMARY KEY (rol_id, permiso_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR NOT NULL,
            email VARCHAR UNIQUE,
            hashed_password VARCHAR,
            is_active BOOLEAN DEFAULT TRUE,
            tipo VARCHAR NOT NULL DEFAULT 'registrado',
            db_password_encrypted VARCHAR,
            rol_id INTEGER REFERENCES roles(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS otp_codes (
            id SERIAL PRIMARY KEY,
            email VARCHAR NOT NULL,
            codigo VARCHAR NOT NULL,
            creado_en TIMESTAMP,
            expira_en TIMESTAMP NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS usuario_github (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER UNIQUE REFERENCES usuarios(id),
            github_username VARCHAR,
            encrypted_token VARCHAR NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS proyectos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR NOT NULL,
            descripcion VARCHAR,
            codigo_acceso VARCHAR UNIQUE,
            fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            fecha_actualizacion TIMESTAMP WITH TIME ZONE,
            lienzo_json TEXT,
            github_repo_url VARCHAR
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS colaboradores_proyecto (
            proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            rol_proyecto VARCHAR NOT NULL DEFAULT 'invitado',
            estado VARCHAR NOT NULL DEFAULT 'pendiente',
            PRIMARY KEY (proyecto_id, usuario_id)
        )
        """,
    )
    for statement in base_tables:
        conn.execute(text(statement))

    # Agregar columna solo si no existe ya
    conn.execute(text("""
        ALTER TABLE usuarios
        ADD COLUMN IF NOT EXISTS etiquetas_habilidades JSONB
    """))

    # Agregar columna deployment_url a proyectos
    conn.execute(text("""
        ALTER TABLE proyectos
        ADD COLUMN IF NOT EXISTS deployment_url VARCHAR
    """))

    # Crear tabla tareas_ia solo si no existe ya
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS tareas_ia (
            id SERIAL PRIMARY KEY,
            proyecto_id INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
            usuario_id  INTEGER NOT NULL REFERENCES usuarios(id)  ON DELETE CASCADE,
            tipo        VARCHAR NOT NULL DEFAULT 'diagrama',
            titulo      VARCHAR NOT NULL,
            descripcion TEXT,
            completada  BOOLEAN NOT NULL DEFAULT false,
            orden       INTEGER NOT NULL DEFAULT 0
        )
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS tareas_ia"))
    conn.execute(text("ALTER TABLE proyectos DROP COLUMN IF EXISTS deployment_url"))
    conn.execute(text("ALTER TABLE usuarios DROP COLUMN IF EXISTS etiquetas_habilidades"))
