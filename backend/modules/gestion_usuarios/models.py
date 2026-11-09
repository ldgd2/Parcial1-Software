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

    # Área de la tarea (ej: 'backend', 'frontend', 'modelado', 'base_de_datos', 'testing', 'general')
    area = Column(String, nullable=True, default="general")

    # CU37: estimación de esfuerzo (la da la IA; si no, se calcula con estimar_tarea)
    estimacion_horas = Column(Integer, nullable=True)
    complejidad = Column(String, nullable=True)   # baja | media | alta
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    completada = Column(Boolean, nullable=False, default=False)
    orden = Column(Integer, nullable=False, default=0)

    usuario = relationship("Usuario")


# ─── CU37: estimación de esfuerzo de tareas ─────────────────────────────────

_COMPLEJIDADES = ("baja", "media", "alta")
# Ojo: palabras de *trabajo* complejo, no nombres de clases ("Modelar Pago" no es complejo; "integrar pagos" sí)
_PALABRAS_ALTA = ("integrar", "integración", "seguridad", "autentic", "pasarela", "migr", "despleg", "arquitectura",
                  "optimiz", "concurren", "sincroniz", "tiempo real", "refactor")
_PALABRAS_BAJA = ("renombrar", "documentar", "revisar", "ajustar", "corregir texto", "estilo", "color")


def estimar_tarea(tipo=None, titulo="", descripcion="", horas_ia=None, complejidad_ia=None):
    """
    Devuelve (horas, complejidad). Usa lo que propuso la IA si es válido; si no, una regla simple:
    diagrama 2 h, desarrollo 4 h, ajustado por palabras clave y largo de la descripción.
    """
    complejidad = str(complejidad_ia or "").strip().lower()
    try:
        horas = int(round(float(horas_ia)))
    except (TypeError, ValueError):
        horas = None
    if horas is not None and 1 <= horas <= 80 and complejidad in _COMPLEJIDADES:
        return horas, complejidad

    texto = f"{titulo or ''} {descripcion or ''}".lower()
    if any(p in texto for p in _PALABRAS_ALTA) or len(descripcion or "") > 280:
        calc = "alta"
    elif any(p in texto for p in _PALABRAS_BAJA):
        calc = "baja"
    else:
        calc = "media"
    complejidad = complejidad if complejidad in _COMPLEJIDADES else calc
    if horas is None or not (1 <= horas <= 80):
        base = 2 if (tipo or "") == "diagrama" else 4
        horas = {"baja": max(1, base // 2), "media": base, "alta": base * 2}[complejidad]
    return horas, complejidad


from sqlalchemy import event as _event  # noqa: E402


@_event.listens_for(TareaIA, "before_insert")
def _completar_estimacion(mapper, connection, tarea):
    """Toda tarea que se guarda sin estimación (p. ej. creada a mano) recibe una."""
    if tarea.estimacion_horas is None or not tarea.complejidad:
        h, c = estimar_tarea(tarea.tipo, tarea.titulo, tarea.descripcion, tarea.estimacion_horas, tarea.complejidad)
        tarea.estimacion_horas = tarea.estimacion_horas or h
        tarea.complejidad = tarea.complejidad or c
