from sqlalchemy import BigInteger, Boolean, Column, Computed, Integer, String, DateTime, ForeignKey, Index, Text, JSON, text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base


class ContextoIAProyecto(Base):
    """
    Persistencia del estado cognitivo, memoria episódica comprimida y registro
    de correcciones de la IA para un proyecto colaborativo.
    """
    __tablename__ = "contextos_ia_proyecto"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    
    dominio = Column(String, nullable=False, default="Sistema de Software")
    resumen_acumulado = Column(Text, nullable=False, default="")
    
    # Lista compacta de eventos episódicos: [{"ts": int, "intent": str, "cmd": str, "delta": str, "summary": str}]
    historial_comprimido = Column(JSON, nullable=False, default=list)
    
    # Registro de correcciones y notas pendientes: [{"id": str, "target": str, "text": str, "estado": str}]
    correcciones = Column(JSON, nullable=False, default=list)
    
    # Instantánea ultra-compacta del diagrama en formato Hyper-DSL
    snapshot_dsl = Column(Text, nullable=False, default="")
    
    # Estadísticas de ahorro de tokens y métricas de sesión
    tokens_ahorrados_estimados = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    proyecto = relationship("Proyecto")



class VersionContextoIA(Base):
    """
    Historial completo de interacciones de la IA con la versión del diagrama
    ANTES y DESPUÉS de cada cambio. Permite previsualizar y restaurar versiones.

    A diferencia de `historial_comprimido` (limitado a 15 eventos para ahorrar
    tokens en el prompt), aquí se conservan todas las interacciones.
    """
    __tablename__ = "versiones_contexto_ia"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)

    ts = Column(Integer, nullable=False)                 # Unix, igual que el evento episódico
    intent = Column(String, nullable=False, default="GENERAL")
    cmd = Column(Text, nullable=False, default="")       # instrucción del usuario (completa)
    resumen = Column(Text, nullable=False, default="")   # resumen de la IA
    delta = Column(String, nullable=False, default="")   # "+A | ~B | -C"
    autor = Column(String, nullable=True)                # nombre de quien pidió el cambio

    # DiagramState del frontend: {"nodes": [...], "relations": [...]}
    estado_antes = Column(JSONB, nullable=True)
    estado_despues = Column(JSONB, nullable=True)

    # Propuesta de la IA pendiente de aprobación: {nodes, relations, deletedNodes, deletedRelations, summary}
    propuesta = Column(JSONB, nullable=True)
    # None (no es propuesta) | 'pendiente' | 'aprobada' | 'rechazada'
    estado_propuesta = Column(String, nullable=True)
    decidida_por = Column(String, nullable=True)            # nombre de quien aprobó / rechazó
    decidida_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    decidida_en = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_versiones_contexto_ia_proyecto", "proyecto_id", "id"),
    )


# Texto indexado para la búsqueda en español (mismo SQL que la migración c1d2e3f4a5b6)
_BUSQUEDA_MEMORIA = (
    "to_tsvector('spanish', coalesce(topic_key, '') || ' ' || coalesce(titulo, '') || ' ' || "
    "coalesce(que, '') || ' ' || coalesce(por_que, '') || ' ' || coalesce(donde, '') || ' ' || "
    "coalesce(aprendido, ''))"
)


class MemoriaIA(Base):
    """
    Memoria del proyecto al estilo Engram: observaciones elegidas (no el chat completo).

    - tipo: decision | restriccion | convencion | correccion | rechazo
    - topic_key: tema estable ("entidades/cliente"); guardar otra observación con el mismo
      tema la REEMPLAZA (la anterior queda con vigente=False y se conserva como historial).
    - en_conflicto: la nueva contradice a la anterior (p. ej. se aprobó y luego se rechazó
      lo mismo); una persona decide cuál vale.
    """
    __tablename__ = "memorias_ia"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)

    tipo = Column(String, nullable=False, default="decision")
    topic_key = Column(String, nullable=False)
    titulo = Column(String, nullable=False, default="")
    que = Column(Text, nullable=False, default="")         # Qué se decidió / qué pasa
    por_que = Column(Text, nullable=False, default="")     # Por qué
    donde = Column(Text, nullable=False, default="")       # Dónde aplica (clase, área)
    aprendido = Column(Text, nullable=False, default="")   # Qué debe tener en cuenta la IA

    origen = Column(String, nullable=False, default="manual")  # aprobacion | rechazo | manual
    version_id = Column(BigInteger, ForeignKey("versiones_contexto_ia.id", ondelete="SET NULL"), nullable=True)
    autor = Column(String, nullable=True)

    vigente = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    reemplaza_id = Column(BigInteger, ForeignKey("memorias_ia.id", ondelete="SET NULL"), nullable=True)
    en_conflicto = Column(Boolean, nullable=False, default=False, server_default=text("false"))

    busqueda = Column(TSVECTOR, Computed(_BUSQUEDA_MEMORIA, persisted=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_memorias_ia_proyecto", "proyecto_id", "vigente"),
        Index("ix_memorias_ia_busqueda", "busqueda", postgresql_using="gin"),
        # Un solo recuerdo vigente por tema
        Index("ux_memorias_ia_tema_vigente", "proyecto_id", "topic_key", unique=True,
              postgresql_where=text("vigente")),
    )
