from rich.table import Table
from backend.cli.console import console
from backend.cli.async_runner import ejecutar_async
from .db_executor import obtener_todos_los_tokens


def ejecutar() -> None:
    console.print("\n[bold cyan]=== DISPOSITIVOS Y TOKENS REGISTRADOS ===[/bold cyan]\n")
    tokens = ejecutar_async(obtener_todos_los_tokens())

    if not tokens:
        console.print("[yellow]No hay tokens de dispositivos registrados en la base de datos.[/yellow]")
        return

    tabla = Table(title=f"Total Registrados: {len(tokens)}")
    tabla.add_column("UID", justify="right", style="cyan")
    tabla.add_column("Usuario", style="white")
    tabla.add_column("Plataforma", style="green", justify="center")
    tabla.add_column("Origen", style="dim")
    tabla.add_column("Device Token FCM", style="magenta")

    for t in tokens:
        raw_token = t["token"]
        token_preview = f"{raw_token[:20]}...{raw_token[-10:]}" if len(raw_token) > 35 else raw_token
        tabla.add_row(
            str(t["usuario_id"]),
            t["usuario"],
            t["plataforma"],
            t["fuente"],
            token_preview,
        )

    console.print(tabla)
