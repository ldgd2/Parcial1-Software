import os
import sys
from pathlib import Path
from typing import Dict

from .menu import ejecutar_comando_alembic, console, BACKEND_DIR


def _load_env(env_path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not env_path.is_file():
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
    user = env.get("DB_USER", "")
    password = env.get("DB_PASSWORD", "")
    host = env.get("DB_IP", "127.0.0.1")
    port = env.get("DB_PORT", "5432")
    dbname = env.get("DB_NAME", "")
    auth = f"{user}:{password}" if password else user
    return f"postgresql://{auth}@{host}:{port}/{dbname}"


def _delete_orphan(conn_str: str, orphan_rev: str) -> None:
    try:
        import psycopg2
    except ImportError:
        console.print("[bold red]psycopg2 no está instalado. Instálalo en el entorno virtual.[/bold red]")
        sys.exit(1)
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("DELETE FROM alembic_version WHERE version_num = %s", (orphan_rev,))
    conn.close()
    console.print(f"[dim]Entrada orphan {orphan_rev} eliminada de alembic_version.[/dim]")


def fix_state() -> None:
    """Elimina la revisión huérfana y sella la BD al head actual."""
    env_path = Path(BACKEND_DIR).parent / ".env"
    env = _load_env(env_path)
    conn_str = _build_conn_str(env)
    orphan_rev = "e3f4a5b6c7d8"
    _delete_orphan(conn_str, orphan_rev)
    ok, _ = ejecutar_comando_alembic(["stamp", "head"], mostrar=True)
    if ok:
        console.print("[bold green]Stamp a head ejecutado con éxito después de la reparación.[/bold green]")
    else:
        console.print("[bold red]Falló el stamp a head después de la reparación.[/bold red]")

