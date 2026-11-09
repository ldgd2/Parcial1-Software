import os
import sys
import subprocess
from pathlib import Path
from typing import Dict


def load_env(env_path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not env_path.is_file():
        sys.exit(f".env file not found at {env_path}")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def build_conn_str(env: Dict[str, str]) -> str:
    user = env.get("DB_USER", "")
    password = env.get("DB_PASSWORD", "")
    host = env.get("DB_IP", "127.0.0.1")
    port = env.get("DB_PORT", "5432")
    dbname = env.get("DB_NAME", "")
    auth = f"{user}:{password}" if password else user
    return f"postgresql://{auth}@{host}:{port}/{dbname}"


def delete_orphan_version(conn_str: str, orphan_rev: str) -> None:
    try:
        import psycopg2
    except ImportError:
        sys.exit("psycopg2 is required to run this script. Install it in the virtual environment.")
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM alembic_version WHERE version_num = %s",
            (orphan_rev,)
        )
    conn.close()
    print(f"Deleted orphan revision {orphan_rev} from alembic_version.")


def run_alembic_cmd(alembic_cfg: Path, cmd: str) -> None:
    result = subprocess.run(
        ["python", "-m", "alembic", "-c", str(alembic_cfg), cmd],
        capture_output=True,
        text=True,
        check=False,
    )
    print(f"alembic {cmd} output:\n{result.stdout}\n{result.stderr}")


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    env_path = project_root / ".env"
    env = load_env(env_path)
    conn_str = build_conn_str(env)
    orphan_rev = "e3f4a5b6c7d8"
    delete_orphan_version(conn_str, orphan_rev)
    alembic_cfg = project_root / "backend" / "alembic.ini"
    for cmd in ("heads", "current"):
        run_alembic_cmd(alembic_cfg, cmd)


if __name__ == "__main__":
    main()

