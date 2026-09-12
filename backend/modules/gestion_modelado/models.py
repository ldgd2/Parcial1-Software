from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from backend.core.database import Base


class DiagramElement(Base):
    """
    CU8 — Elemento del diagrama.
    Tipos: class | interface | abstract | enum | note
    """
    __tablename__ = "diagram_elements"

    id          = Column(String,  primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    type        = Column(String(20), nullable=False)

    nombre = Column(String(255), nullable=False, default="NuevaClase")
    color  = Column(String(20),  nullable=True)

    # Posición y dimensiones — volátiles, NO versionadas semánticamente
    pos_x  = Column(Integer, nullable=True, default=200)
    pos_y  = Column(Integer, nullable=True, default=200)
    width  = Column(Integer, nullable=True, default=220)

    # Contenido completo (atributos, métodos, valores enum, texto nota)
    content = Column(JSONB, nullable=False, default=dict)

    # VCS
    version = Column(Integer, nullable=False, default=0)
    hash    = Column(String(64), nullable=False, default="")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DiagramRelation(Base):
    """
    CU9 — Relación entre dos elementos del diagrama.
    Tipos: association | inheritance | composition | aggregation | dependency | realization | directed
    """
    __tablename__ = "diagram_relations"

    id          = Column(String,  primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    type        = Column(String(20), nullable=False)

    source_id = Column(String, ForeignKey("diagram_elements.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String, ForeignKey("diagram_elements.id", ondelete="CASCADE"), nullable=False)

    label        = Column(String(255), nullable=True, default="")
    source_label = Column(String(50),  nullable=True, default="")
    target_label = Column(String(50),  nullable=True, default="")

    # VCS
    version = Column(Integer, nullable=False, default=0)
    hash    = Column(String(64), nullable=False, default="")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
