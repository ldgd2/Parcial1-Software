import sys
from pathlib import Path
from typing import Dict

from .menu import ejecutar_comando_alembic, console, BACKEND_DIR


def _load_env(env_path: Path) -> Dict[str, str]:
    """Load key/value pairs from a .env file.

    Returns a dictionary with the variables. If the file does not exist,
    the function attempts to fall back to ``../Movil/.env``; if that also
    fails the process exits with an error message.
    """
    env: Dict[str, str] = {}
    if not env_path.is_file():
        # try alternative location used in the project
        alt_path = Path(BACKEND_DIR).parent / "Movil" / ".env"
        if alt_path.is_file():
            env_path = alt_path
            console.print(f"[dim]Usando .env alternativo en {env_path}[/dim]")
        else:
            console.print(f"[bold red].env no encontrado en {env_path}[/bold red]")
            sys.exit(1)
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def _build_conn_str(env: Dict[str, str]) -> str:
    """Construct a PostgreSQL connection string from env variables."""
    user = env.get("DB_USER", "")
    password = env.get("DB_PASSWORD", "")
    host = env.get("DB_IP", "127.0.0.1")
    port = env.get("DB_PORT", "5432")
    dbname = env.get("DB_NAME", "")
    auth = f"{user}:{password}" if password else user
    return f"postgresql://{auth}@{host}:{port}/{dbname}"


def _delete_orphan(conn_str: str, orphan_rev: str) -> bool:
    """Remove the orphan revision from the ``alembic_version`` table."""
    try:
        import psycopg2
    except ImportError:
        console.print("[bold red]psycopg2 no está instalado. Instálalo en el entorno virtual.[/bold red]")
        sys.exit(1)
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("DELETE FROM alembic_version WHERE version_num = %s", (orphan_rev,))
        borradas = cur.rowcount
    conn.close()
    if borradas:
        console.print(f"[dim]Entrada orphan {orphan_rev} eliminada de alembic_version.[/dim]")
    return borradas > 0


def fix_state() -> None:
    """Auto‑repair the Alembic migration state.

    1. Load database credentials from ``.env``.
    2. Delete the orphan revision ``e3f4a5b6c7d8`` (its file was removed from the chain).
    3. If the DB was on it, stamp its parent ``d2e3f4a5b6c7`` (lo último que esa base sí tenía).
    4. Apply the pending migrations (upgrade head).

    Antes se hacía `stamp head`: marcaba la base como al día SIN crear lo que faltaba (por ejemplo
    las columnas de permisos o plantillas_proyecto). Las migraciones posteriores a d2e3f4a5b6c7 son
    idempotentes (IF NOT EXISTS), así que aplicarlas sobre una base que ya tiene parte es seguro.
    """
    # Misma conexión que el backend y alembic (settings): respeta variables de entorno y
    # contraseñas con caracteres especiales, que armándola a mano desde el .env fallaban.
    from backend.core.config import settings
    conn_str = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    orphan_rev = "e3f4a5b6c7d8"
    if _delete_orphan(conn_str, orphan_rev):
        ok, _ = ejecutar_comando_alembic(["stamp", "d2e3f4a5b6c7"], mostrar=True)
        if not ok:
            console.print("[bold red]Falló el stamp a d2e3f4a5b6c7.[/bold red]")
            return
    ok, _ = ejecutar_comando_alembic(["upgrade", "head"], mostrar=True)
    if ok:
        console.print("[bold green]Migraciones al día (upgrade head).[/bold green]")
    else:
        console.print("[bold red]Falló el upgrade a head.[/bold red]")


if __name__ == "__main__":
    fix_state()
