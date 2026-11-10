import uuid
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, JSON, text
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

    # CU38: permiso de un miembro (no anfitrión) dentro del proyecto: 'edit' (editor) | 'view' (lector).
    # Se guarda aquí para que no se pierda al reiniciar el servidor ni al reconectarse a la sala.
    permiso = Column(String(10), nullable=False, default="edit", server_default="edit")
    # CU38: Permisos persistentes por colaborador
    permiso_rol = Column(String(20), nullable=False, default="editor", server_default="editor")  # 'editor' | 'lector'
    puede_editar = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    puede_eliminar = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    puede_exportar = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    puede_usar_ia = Column(Boolean, nullable=False, default=True, server_default=text("true"))

    # Rol asignado por la arquitectura o IA en este proyecto específico (ej: Backend Architect, Frontend Lead, DBA, QA)
    rol_ia = Column(String, nullable=True, default=None)

    # Áreas de responsabilidad en este proyecto (ej: ["backend", "api"], ["frontend", "ui"], ["base_de_datos"])
    areas = Column(JSON, nullable=True, default=None)

    # Lista o detalle de responsabilidades específicas asignadas
    responsabilidades = Column(JSON, nullable=True, default=None)
    
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
    
    # URL del repositorio de GitHub vinculado
    github_repo_url = Column(String, nullable=True, default=None)
    
    # URL del despliegue en el servidor
    deployment_url = Column(String, nullable=True, default=None)
    
    # Carga eager o lazy según necesidad
    colaboradores = relationship("ColaboradorProyecto", back_populates="proyecto", cascade="all, delete-orphan")
