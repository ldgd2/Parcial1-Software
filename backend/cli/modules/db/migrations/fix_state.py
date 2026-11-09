import os
if __name__ == "__main__":
    fix_state()
import sys
if __name__ == "__main__":
    fix_state()
from pathlib import Path
if __name__ == "__main__":
    fix_state()
from typing import Dict
if __name__ == "__main__":
    fix_state()

if __name__ == "__main__":
    fix_state()
from .menu import ejecutar_comando_alembic, console, BACKEND_DIR
if __name__ == "__main__":
    fix_state()

if __name__ == "__main__":
    fix_state()

if __name__ == "__main__":
    fix_state()
def _load_env(env_path: Path) -> Dict[str, str]:
if __name__ == "__main__":
    fix_state()
    env: Dict[str, str] = {}
if __name__ == "__main__":
    fix_state()
    if not env_path.is_file():
if __name__ == "__main__":
    fix_state()
        console.print(f"[bold red].env no encontrado en {env_path}[/bold red]")
if __name__ == "__main__":
    fix_state()
        sys.exit(1)
if __name__ == "__main__":
    fix_state()
    for line in env_path.read_text(encoding="utf-8").splitlines():
if __name__ == "__main__":
    fix_state()
        line = line.strip()
if __name__ == "__main__":
    fix_state()
        if not line or line.startswith("#"):
if __name__ == "__main__":
    fix_state()
            continue
if __name__ == "__main__":
    fix_state()
        if "=" not in line:
if __name__ == "__main__":
    fix_state()
            continue
if __name__ == "__main__":
    fix_state()
        key, value = line.split("=", 1)
if __name__ == "__main__":
    fix_state()
        env[key.strip()] = value.strip()
if __name__ == "__main__":
    fix_state()
    return env
if __name__ == "__main__":
    fix_state()

if __name__ == "__main__":
    fix_state()

if __name__ == "__main__":
    fix_state()
def _build_conn_str(env: Dict[str, str]) -> str:
if __name__ == "__main__":
    fix_state()
    user = env.get("DB_USER", "")
if __name__ == "__main__":
    fix_state()
    password = env.get("DB_PASSWORD", "")
if __name__ == "__main__":
    fix_state()
    host = env.get("DB_IP", "127.0.0.1")
if __name__ == "__main__":
    fix_state()
    port = env.get("DB_PORT", "5432")
if __name__ == "__main__":
    fix_state()
    dbname = env.get("DB_NAME", "")
if __name__ == "__main__":
    fix_state()
    auth = f"{user}:{password}" if password else user
if __name__ == "__main__":
    fix_state()
    return f"postgresql://{auth}@{host}:{port}/{dbname}"
if __name__ == "__main__":
    fix_state()

if __name__ == "__main__":
    fix_state()

if __name__ == "__main__":
    fix_state()
def _delete_orphan(conn_str: str, orphan_rev: str) -> None:
if __name__ == "__main__":
    fix_state()
    try:
if __name__ == "__main__":
    fix_state()
        import psycopg2
if __name__ == "__main__":
    fix_state()
    except ImportError:
if __name__ == "__main__":
    fix_state()
        console.print("[bold red]psycopg2 no está instalado. Instálalo en el entorno virtual.[/bold red]")
if __name__ == "__main__":
    fix_state()
        sys.exit(1)
if __name__ == "__main__":
    fix_state()
    conn = psycopg2.connect(conn_str)
if __name__ == "__main__":
    fix_state()
    conn.autocommit = True
if __name__ == "__main__":
    fix_state()
    with conn.cursor() as cur:
if __name__ == "__main__":
    fix_state()
        cur.execute("DELETE FROM alembic_version WHERE version_num = %s", (orphan_rev,))
if __name__ == "__main__":
    fix_state()
    conn.close()
if __name__ == "__main__":
    fix_state()
    console.print(f"[dim]Entrada orphan {orphan_rev} eliminada de alembic_version.[/dim]")
if __name__ == "__main__":
    fix_state()

if __name__ == "__main__":
    fix_state()

if __name__ == "__main__":
    fix_state()
def fix_state() -> None:
if __name__ == "__main__":
    fix_state()
    """Elimina la revisión huérfana y sella la BD al head actual."""
if __name__ == "__main__":
    fix_state()
    env_path = Path(BACKEND_DIR).parent / ".env"
if __name__ == "__main__":
    fix_state()
    env = _load_env(env_path)
if __name__ == "__main__":
    fix_state()
    conn_str = _build_conn_str(env)
if __name__ == "__main__":
    fix_state()
    orphan_rev = "e3f4a5b6c7d8"
if __name__ == "__main__":
    fix_state()
    _delete_orphan(conn_str, orphan_rev)
if __name__ == "__main__":
    fix_state()
    ok, _ = ejecutar_comando_alembic(["stamp", "head"], mostrar=True)
if __name__ == "__main__":
    fix_state()
    if ok:
if __name__ == "__main__":
    fix_state()
        console.print("[bold green]Stamp a head ejecutado con éxito después de la reparación.[/bold green]")
if __name__ == "__main__":
    fix_state()
    else:
if __name__ == "__main__":
    fix_state()
        console.print("[bold red]Falló el stamp a head después de la reparación.[/bold red]")
if __name__ == "__main__":
    fix_state()

if __name__ == "__main__":
    fix_state()
