from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.sql import func

from backend.core.database import Base


class Notificacion(Base):
    """CU39: aviso para un usuario (se ve en la campana y, si hay Firebase, llega como push)."""
    __tablename__ = "notificaciones"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=True)
    # propuesta_pendiente | propuesta_decidida | tarea_asignada | solicitud_union | solicitud_aprobada | comentario
    tipo = Column(String(40), nullable=False)
    titulo = Column(String(160), nullable=False)
    mensaje = Column(Text, nullable=False, default="", server_default="")
    url = Column(String(300), nullable=True)            # ruta del frontend a la que lleva el aviso
    leida = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (Index("ix_notificaciones_usuario_leida", "usuario_id", "leida", "created_at"),)


class DispositivoPush(Base):
    """Token de Firebase Cloud Messaging de un navegador o del móvil."""
    __tablename__ = "dispositivos_push"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(512), nullable=False, unique=True)
    plataforma = Column(String(20), nullable=False, default="web", server_default="web")   # web | android | ios
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
