from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
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

