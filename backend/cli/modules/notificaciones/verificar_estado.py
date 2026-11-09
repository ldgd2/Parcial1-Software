import os
from pathlib import Path
from rich.table import Table
from backend.cli.console import console

try:
    import firebase_admin
    _HAS_SDK = True
except ImportError:
    firebase_admin = None
    _HAS_SDK = False


def ejecutar() -> None:
    console.print("\n[bold cyan]=== ESTADO DE FIREBASE ADMIN SDK ===[/bold cyan]\n")

    if not _HAS_SDK or firebase_admin is None:
        console.print("[bold red]firebase-admin no esta instalado en este entorno de Python.[/bold red]")
        console.print("[dim]Ejecuta: pip install firebase-admin[/dim]\n")
        return

    inicializado = bool(firebase_admin._apps)
    estado_str = "[bold green]INICIALIZADO[/bold green]" if inicializado else "[bold red]NO INICIALIZADO[/bold red]"
    console.print(f"Estado de la app Firebase: {estado_str}")

    env_var = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    console.print(f"Variable FIREBASE_SERVICE_ACCOUNT: {env_var or '(no configurada)'}")

    backend_root = Path(__file__).resolve().parents[4]
    config_dir = (
        Path(__file__).resolve().parents[3]
        / "modules"
        / "gestion_asistencia_ia"
        / "notificaciones"
        / "config"
    )

    tabla = Table(title="Rutas de Credenciales Detectadas")
    tabla.add_column("Ubicacion", style="cyan")
    tabla.add_column("Existe", justify="center")

    rutas = [
        ("Variable de Entorno", Path(env_var) if env_var else None),
        ("Carpeta config del modulo", config_dir / "diagramador-firebase-service.json"),
        ("backend/firebase-service-account.json", backend_root / "backend" / "firebase-service-account.json"),
        ("firebase-service-account.json (raiz)", backend_root / "firebase-service-account.json"),
    ]

    if config_dir.is_dir():
        for extra_json in config_dir.glob("*.json"):
            if extra_json.name != "diagramador-firebase-service.json":
                rutas.append((f"config/{extra_json.name}", extra_json))

    for desc, path in rutas:
        if path is None:
            tabla.add_row(desc, "[dim]-[/dim]")
        else:
            existe = path.is_file()
            simbolo = "[bold green]SI[/bold green]" if existe else "[bold red]NO[/bold red]"
            tabla.add_row(f"{desc}\n[dim]{path}[/dim]", simbolo)

    console.print(tabla)
