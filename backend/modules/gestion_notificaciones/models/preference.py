from sqlalchemy import Boolean, Column, DateTime, Integer, text
from sqlalchemy.sql import func

from backend.core.database import Base

class UserNotificationPreference(Base):
    """CU39: preferencias de notificación por usuario.
    Cada fila define qué tipos de eventos debe recibir el usuario y si está en modo silencioso.
    """
    __tablename__ = "user_notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    receive_position_updates = Column(Boolean, nullable=False, server_default=text("false"), default=False)
    receive_semantic_changes = Column(Boolean, nullable=False, server_default=text("true"), default=True)
    receive_comments = Column(Boolean, nullable=False, server_default=text("false"), default=False)
    receive_invitations = Column(Boolean, nullable=False, server_default=text("true"), default=True)
    receive_task_assignments = Column(Boolean, nullable=False, server_default=text("true"), default=True)
    quiet_mode = Column(Boolean, nullable=False, server_default=text("false"), default=False)
    quiet_mode_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

