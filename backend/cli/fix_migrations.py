import argparse
import subprocess
import sys
from pathlib import Path

def run_alembic(alembic_cfg: Path, args: list[str]):
    cmd = [sys.executable, "-m", "alembic", "-c", str(alembic_cfg)] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Running: {' '.join(cmd)}")
    print(f"Return code: {result.returncode}")
    if result.stdout:
        print("STDOUT:\n" + result.stdout)
    if result.stderr:
        print("STDERR:\n" + result.stderr)
    result.check_returncode()

def main():
    parser = argparse.ArgumentParser(description="Fix Alembic multiple‑head issue by removing obsolete revision and stamping DB.")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2], help="Root of the project (default: two levels up from this script).")
    parser.add_argument("--obsolete-revision", type=str, default="e3f4a5b6c7d8_create_plantillas_proyecto.py", help="Filename of the obsolete migration revision to delete.")
    args = parser.parse_args()

    project_root = args.project_root
    alembic_cfg = project_root / "backend" / "alembic.ini"
    versions_dir = project_root / "backend" / "alembic" / "versions"
    obsolete_path = versions_dir / args.obsolete_revision

    if obsolete_path.is_file():
        obsolete_path.unlink()
        print(f"Removed obsolete migration file: {obsolete_path.name}")
    else:
        print("Obsolete migration file not found; skipping deletion.")

    # Verify single head
    run_alembic(alembic_cfg, ["heads"])
    # Stamp DB to head
    run_alembic(alembic_cfg, ["stamp", "head"])
    # Show current DB version
    run_alembic(alembic_cfg, ["current"])

if __name__ == "__main__":
    main()

