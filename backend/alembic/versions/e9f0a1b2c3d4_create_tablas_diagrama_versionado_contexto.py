"""create tablas que solo existian via create_all: versionado, diagrama, comentarios, contexto IA

Hasta ahora estas tablas se creaban únicamente con Base.metadata.create_all al
arrancar la app, por lo que `alembic upgrade head` (launcher > Migraciones > Up)
dejaba la base incompleta. Todo es idempotente (IF NOT EXISTS), así que es
seguro aplicarla sobre una base que ya tenga estas tablas.

Revision ID: e9f0a1b2c3d4
Revises: b2c3d4e5f6a7
Create Date: 2026-11-08 00:00:00.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'e9f0a1b2c3d4'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


SENTENCIAS = [
    # ── Versionado (backend/modules/gestion_proyectos/versioning/models.py) ──
    """
    CREATE TABLE IF NOT EXISTS git_objects (
        hash        VARCHAR NOT NULL,
        type        VARCHAR NOT NULL,
        content     JSONB NOT NULL,
        created_at  TIMESTAMP WITH TIME ZONE DEFAULT now(),
        PRIMARY KEY (hash)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_git_objects_type ON git_objects (type)",
    "CREATE INDEX IF NOT EXISTS ix_git_objects_hash ON git_objects (hash)",
    """
    CREATE TABLE IF NOT EXISTS commits (
        hash         VARCHAR NOT NULL,
        tree_hash    VARCHAR NOT NULL,
        parent_hash  VARCHAR,
        author       VARCHAR NOT NULL,
        message      VARCHAR NOT NULL,
        created_at   TIMESTAMP WITH TIME ZONE DEFAULT now(),
        PRIMARY KEY (hash),
        FOREIGN KEY (tree_hash) REFERENCES git_objects (hash),
        FOREIGN KEY (parent_hash) REFERENCES commits (hash)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_commits_hash ON commits (hash)",

    # ── Contexto persistente de la IA (backend/modules/gestion_asistencia_ia/models.py) ──
    """
    CREATE TABLE IF NOT EXISTS contextos_ia_proyecto (
        id                          SERIAL NOT NULL,
        proyecto_id                 INTEGER NOT NULL,
        dominio                     VARCHAR NOT NULL,
        resumen_acumulado           TEXT NOT NULL,
        historial_comprimido        JSON NOT NULL,
        correcciones                JSON NOT NULL,
        snapshot_dsl                TEXT NOT NULL,
        tokens_ahorrados_estimados  INTEGER NOT NULL,
        version                     INTEGER NOT NULL,
        fecha_creacion              TIMESTAMP WITH TIME ZONE DEFAULT now(),
        fecha_actualizacion         TIMESTAMP WITH TIME ZONE DEFAULT now(),
        PRIMARY KEY (id),
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id) ON DELETE CASCADE
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_contextos_ia_proyecto_proyecto_id ON contextos_ia_proyecto (proyecto_id)",
    "CREATE INDEX IF NOT EXISTS ix_contextos_ia_proyecto_id ON contextos_ia_proyecto (id)",

    # ── Diagrama (backend/modules/gestion_modelado/models.py) ──
    """
    CREATE TABLE IF NOT EXISTS diagram_elements (
        id           VARCHAR NOT NULL,
        proyecto_id  INTEGER NOT NULL,
        type         VARCHAR(50) NOT NULL,
        nombre       VARCHAR(255) NOT NULL,
        color        VARCHAR(20),
        pos_x        INTEGER,
        pos_y        INTEGER,
        width        INTEGER,
        content      JSONB NOT NULL,
        version      INTEGER NOT NULL,
        hash         VARCHAR(64) NOT NULL,
        created_at   TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at   TIMESTAMP WITH TIME ZONE DEFAULT now(),
        PRIMARY KEY (id),
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_diagram_elements_proyecto_id ON diagram_elements (proyecto_id)",
    "CREATE INDEX IF NOT EXISTS ix_diagram_elements_id ON diagram_elements (id)",
    """
    CREATE TABLE IF NOT EXISTS diagram_relations (
        id            VARCHAR NOT NULL,
        proyecto_id   INTEGER NOT NULL,
        type          VARCHAR(50) NOT NULL,
        source_id     VARCHAR NOT NULL,
        target_id     VARCHAR NOT NULL,
        label         VARCHAR(255),
        source_label  VARCHAR(50),
        target_label  VARCHAR(50),
        version       INTEGER NOT NULL,
        hash          VARCHAR(64) NOT NULL,
        created_at    TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at    TIMESTAMP WITH TIME ZONE DEFAULT now(),
        PRIMARY KEY (id),
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id),
        FOREIGN KEY (source_id) REFERENCES diagram_elements (id) ON DELETE CASCADE,
        FOREIGN KEY (target_id) REFERENCES diagram_elements (id) ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_diagram_relations_proyecto_id ON diagram_relations (proyecto_id)",
    "CREATE INDEX IF NOT EXISTS ix_diagram_relations_id ON diagram_relations (id)",
    """
    CREATE TABLE IF NOT EXISTS diagram_element_comments (
        id             VARCHAR(50) NOT NULL,
        proyecto_id    INTEGER NOT NULL,
        elemento_id    VARCHAR(100) NOT NULL,
        elemento_tipo  VARCHAR(50) NOT NULL,
        autor_id       INTEGER,
        autor_nombre   VARCHAR(100) NOT NULL,
        texto          VARCHAR NOT NULL,
        estado         VARCHAR(20) NOT NULL,
        created_at     TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at     TIMESTAMP WITH TIME ZONE DEFAULT now(),
        PRIMARY KEY (id),
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id) ON DELETE CASCADE,
        FOREIGN KEY (autor_id) REFERENCES usuarios (id) ON DELETE SET NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_diagram_element_comments_proyecto_id ON diagram_element_comments (proyecto_id)",
    "CREATE INDEX IF NOT EXISTS ix_diagram_element_comments_id ON diagram_element_comments (id)",
    "CREATE INDEX IF NOT EXISTS ix_diagram_element_comments_elemento_id ON diagram_element_comments (elemento_id)",
]


def upgrade() -> None:
    conn = op.get_bind()
    for sentencia in SENTENCIAS:
        conn.execute(text(sentencia))


def downgrade() -> None:
    conn = op.get_bind()
    # Orden inverso a las dependencias (FK)
    for tabla in (
        "diagram_element_comments",
        "diagram_relations",
        "diagram_elements",
        "contextos_ia_proyecto",
        "commits",
        "git_objects",
    ):
        conn.execute(text(f"DROP TABLE IF EXISTS {tabla}"))
