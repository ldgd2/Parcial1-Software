import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.core.database import Base

class ColaboradorProyecto(Base):
    """Tabla asociativa con campos extra para manejar roles y estados de aprobación en un proyecto."""
    __tablename__ = "colaboradores_proyecto"
    
    proyecto_id = Column(Integer, ForeignKey("proyectos.id", ondelete="CASCADE"), primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    
    # 'anfitrion' o 'invitado'
    rol_proyecto = Column(String, nullable=False, default="invitado")
    
    # 'pendiente', 'aprobado', 'rechazado'
    estado = Column(String, nullable=False, default="pendiente")
    
    # Relaciones
    proyecto = relationship("Proyecto", back_populates="colaboradores")
    usuario = relationship("Usuario")

class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    
    # UUID para el link de invitación público
    codigo_acceso = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Estado del lienzo de diagramas (JSON serializado)
    lienzo_json = Column(Text, nullable=True, default=None)
    
    # Carga eager o lazy según necesidad
    colaboradores = relationship("ColaboradorProyecto", back_populates="proyecto", cascade="all, delete-orphan")
