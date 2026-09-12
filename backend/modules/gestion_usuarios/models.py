from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
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
