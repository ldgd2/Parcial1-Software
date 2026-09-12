from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from backend.core.database import Base

class GitObject(Base):
    __tablename__ = "git_objects"

    # SHA-256 hash de la data
    hash = Column(String, primary_key=True, index=True)
    
    # Tipo de objeto (e.g. 'class', 'attribute', 'tree')
    type = Column(String, nullable=False, index=True)
    
    # Contenido del objeto JSON
    content = Column(JSONB, nullable=False)
    
    # Fecha de registro (útil para purgado de objetos sin referencias)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Commit(Base):
    __tablename__ = "commits"

    hash = Column(String, primary_key=True, index=True)
    
    # El árbol raíz al que apunta este commit
    tree_hash = Column(String, ForeignKey("git_objects.hash"), nullable=False)
    
    # Hash del commit anterior, nullable si es el primer commit
    parent_hash = Column(String, ForeignKey("commits.hash"), nullable=True)
    
    # Información adicional: autor, mensaje
    author = Column(String, nullable=False)
    message = Column(String, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
