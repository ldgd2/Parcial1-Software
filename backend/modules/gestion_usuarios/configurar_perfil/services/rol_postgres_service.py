"""
Rol de PostgreSQL propio de cada usuario (con él se conectan las BD de sus proyectos desplegados).

Lo usan:
  - POST /configuracion/db, cuando el usuario fija su contraseña.
  - El gestor (`python -m backend.cli` → Base de Datos → Roles PostgreSQL), que da CREATEROLE al
    usuario del backend y re-crea los roles de todas las cuentas con contraseña guardada.

Para crear roles, el usuario con el que se conecta el backend (DB_USER) necesita CREATEROLE
(o ser superusuario). Sin eso ninguna cuenta podía configurar su contraseña.
"""
import re
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SinPermisoCreateRole(Exception):
    """DB_USER no tiene CREATEROLE: ninguna cuenta podrá tener su rol de PostgreSQL."""


def nombre_rol(email: Optional[str]) -> str:
    """Nombre del rol a partir del correo (parte antes de @, solo letras y números)."""
    base = re.sub(r"[^a-zA-Z0-9]", "", (email or "").split("@")[0])
    return base or "user"


async def puede_crear_roles(db: AsyncSession) -> bool:
    fila = (await db.execute(text(
        "SELECT rolcreaterole OR rolsuper FROM pg_roles WHERE rolname = current_user"
    ))).first()
    return bool(fila and fila[0])


async def asegurar_rol(db: AsyncSession, email: Optional[str], password: str) -> str:
    """Crea el rol (LOGIN) o le cambia la contraseña. Dentro de un SAVEPOINT: si falla, la
    transacción del llamador sigue viva. Lanza SinPermisoCreateRole si falta el permiso."""
    rol = nombre_rol(email)                        # solo [a-z0-9]: seguro como identificador
    clave = password.replace("'", "''")            # literal SQL
    sql = text(
        "DO $$ BEGIN "
        f"IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{rol}') THEN "
        f"CREATE ROLE \"{rol}\" WITH LOGIN ENCRYPTED PASSWORD '{clave}'; "
        f"ELSE ALTER ROLE \"{rol}\" WITH LOGIN PASSWORD '{clave}'; "
        "END IF; END $$;"
    )
    try:
        async with db.begin_nested():
            await db.execute(sql)
    except Exception as e:
        mensaje = str(e)
        if "CREATEROLE" in mensaje or "permission denied" in mensaje.lower():
            raise SinPermisoCreateRole(rol) from None
        raise
    return rol
