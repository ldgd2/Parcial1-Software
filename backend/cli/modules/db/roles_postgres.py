"""
Gestor → Base de Datos → Roles PostgreSQL de usuarios.

1. Da CREATEROLE al usuario con el que se conecta el backend (DB_USER del .env), sin escribir
   nombres a mano. Sin ese permiso NINGUNA cuenta podía configurar su contraseña de PostgreSQL.
2. Re-crea el rol de cada cuenta que ya tiene contraseña guardada (por si se guardó sin rol).
"""
import os
import re
import subprocess

from backend.cli.async_runner import ejecutar_async
from backend.cli.console import console


def _es_local(host: str) -> bool:
    return host in ("localhost", "127.0.0.1", "::1", "")


def _dar_createrole_con_sudo(db_user: str) -> bool:
    """En el VPS: ALTER ROLE ... CREATEROLE como el superusuario `postgres` del sistema."""
    if not re.fullmatch(r"[A-Za-z0-9_]+", db_user):
        console.print(f"[red]Nombre de usuario de BD inesperado: {db_user!r}[/red]")
        return False
    comando = ["sudo", "-u", "postgres", "psql", "-v", "ON_ERROR_STOP=1",
               "-c", f'ALTER ROLE "{db_user}" CREATEROLE;']
    console.print(f"[cyan]$ sudo -u postgres psql -c 'ALTER ROLE \"{db_user}\" CREATEROLE;'[/cyan]")
    return subprocess.run(comando).returncode == 0


async def _estado():
    from backend.core.database import AsyncSessionLocal
    from backend.modules.gestion_usuarios.configurar_perfil.services.rol_postgres_service import puede_crear_roles
    async with AsyncSessionLocal() as db:
        return await puede_crear_roles(db)


async def _sincronizar():
    import backend.main  # noqa: F401  (registra los modelos)
    from sqlalchemy import select
    from backend.core.database import AsyncSessionLocal
    from backend.core.security import desencriptar_dato
    from backend.modules.gestion_usuarios.models import Usuario
    from backend.modules.gestion_usuarios.configurar_perfil.services.rol_postgres_service import asegurar_rol

    ok, fallos = [], []
    async with AsyncSessionLocal() as db:
        usuarios = (await db.execute(
            select(Usuario).where(Usuario.db_password_encrypted.isnot(None))
        )).scalars().all()
        for u in usuarios:
            try:
                clave = desencriptar_dato(u.db_password_encrypted)
                ok.append(await asegurar_rol(db, u.email, clave))
            except Exception as e:
                fallos.append((u.email, type(e).__name__))
        await db.commit()
    return ok, fallos


def reparar_roles():
    from backend.core.config import settings

    console.print(f"\n[bold]Usuario de BD del backend:[/bold] {settings.DB_USER} @ {settings.DB_IP}")
    try:
        puede = ejecutar_async(_estado())
    except Exception as e:
        console.print(f"[red]No se pudo conectar a PostgreSQL: {e}[/red]")
        return

    if puede:
        console.print("[green]✔ Ya tiene CREATEROLE (o es superusuario).[/green]")
    elif os.name != "nt" and _es_local(settings.DB_IP):
        if _dar_createrole_con_sudo(settings.DB_USER) and ejecutar_async(_estado()):
            console.print("[bold green]✔ Permiso CREATEROLE otorgado.[/bold green]")
        else:
            console.print("[bold red]❌ No se pudo otorgar CREATEROLE.[/bold red]")
            return
    else:
        console.print("[yellow]Falta CREATEROLE. Ejecuta como superusuario de PostgreSQL:[/yellow]")
        console.print(f'   ALTER ROLE "{settings.DB_USER}" CREATEROLE;')
        return

    with console.status("[cyan]Sincronizando roles de las cuentas con contraseña guardada..."):
        ok, fallos = ejecutar_async(_sincronizar())
    console.print(f"[green]✔ Roles creados/actualizados: {len(ok)}[/green]" + (f"  ({', '.join(ok)})" if ok else ""))
    for email, error in fallos:
        console.print(f"[red]  • {email}: {error}[/red]")
