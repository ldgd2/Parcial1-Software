from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.core.database import Base

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

    notification = relationship("NotificationToken", back_populates="logs")

