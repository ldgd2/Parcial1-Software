from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from datetime import datetime
from backend.core.database import Base

class NotificationPreference(Base):
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
