from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.core.database import Base, heredar
from backend.core.permissions.models import Rol 

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    tipo = Column(String, nullable=False, default="registrado")
    db_password_encrypted = Column(String, nullable=True)
    etiquetas_habilidades = Column(JSON, nullable=True, default=None)
    
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    rol = relationship("Rol", lazy="selectin")

    __mapper_args__ = {
        "polymorphic_on": tipo,
        "polymorphic_identity": "usuario"
    }

UsuarioRegistrado = heredar(Usuario, "UsuarioRegistrado")
UsuarioAnonimo = heredar(Usuario, "UsuarioAnonimo")

from sqlalchemy import DateTime
import datetime

class OTPCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    codigo = Column(String, nullable=False)
    creado_en = Column(DateTime, default=datetime.datetime.utcnow)
    expira_en = Column(DateTime, nullable=False)

class UsuarioGitHub(Base):
    __tablename__ = "usuario_github"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True)
    github_username = Column(String)
    encrypted_token = Column(String, nullable=False)


class TareaIA(Base):
    """Checklist de tareas generado por la IA para cada colaborador en un proyecto."""
    __tablename__ = "tareas_ia"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)

    # 'diagrama' = tarea dentro del diagramador | 'desarrollo' = tarea externa
    tipo = Column(String, nullable=False, default="diagrama")
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    completada = Column(Boolean, nullable=False, default=False)
    orden = Column(Integer, nullable=False, default=0)

    usuario = relationship("Usuario")
