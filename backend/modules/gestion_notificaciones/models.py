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


# ─── Módulo móvil del líder (antes en gestion_notificaciones) ──
# Tokens FCM enviados por la app Flutter, bitácora de envíos y preferencias por usuario.
from datetime import datetime  # noqa: E402

from sqlalchemy.orm import relationship  # noqa: E402


class NotificationToken(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    device_token = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    logs = relationship("NotificationLog", back_populates="notification", cascade="all, delete-orphan")


class NotificationLog(Base):
    __tablename__ = "notifications_log"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    data = Column(Text)  # JSON string
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    priority = Column(Integer, default=3)  # 1 low - 5 critical
    type = Column(String, nullable=False, default="generic")

    notification = relationship("NotificationToken", back_populates="logs")


class NotificationPreference(Base):
    """Qué tipos de aviso quiere recibir el usuario y si está en modo silencioso."""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True, unique=True)
    receive_position_updates = Column(Boolean, default=False)
    receive_semantic_changes = Column(Boolean, default=True)
    receive_comments = Column(Boolean, default=False)
    receive_invitations = Column(Boolean, default=True)
    receive_task_assignments = Column(Boolean, default=True)
    quiet_mode = Column(Boolean, default=False)
    quiet_mode_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
