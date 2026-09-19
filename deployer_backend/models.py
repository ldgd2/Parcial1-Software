from sqlalchemy import Column, Integer, String, DateTime, func
from core.database import Base

class Deployment(Base):
    __tablename__ = "deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True)
    repo_url = Column(String, index=True)
    port = Column(Integer, unique=True, index=True)
    pid = Column(Integer, nullable=True) # Process ID in Linux/Windows
    status = Column(String) # 'deploying', 'running', 'failed', 'stopped'
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
