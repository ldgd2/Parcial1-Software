import asyncio
from rich.table import Table
from backend.cli.console import console
from .db_executor import obtener_historial_logs


def ejecutar() -> None:
    console.print("\n[bold cyan]=== HISTORIAL DE ENVIOS PUSH ===[/bold cyan]\n")
    logs = asyncio.run(obtener_historial_logs(limite=20))

    if not logs:
        console.print("[yellow]No hay registros en notifications_log.[/yellow]")
        return

    tabla = Table(title=f"Ultimos {len(logs)} Envios")
    tabla.add_column("ID", justify="right", style="cyan")
    tabla.add_column("UID", justify="right", style="white")
    tabla.add_column("Titulo", style="white")
    tabla.add_column("Cuerpo", style="dim")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Fecha", style="green")

    for l in logs:
        estado_str = "[bold green]ENVIADO[/bold green]" if l["enviado"] else "[bold red]FALLO[/bold red]"
        tabla.add_row(
            str(l["id"]),
            str(l["usuario_id"]),
            l["titulo"],
            l["cuerpo"][:40] + ("..." if len(l["cuerpo"]) > 40 else ""),
            estado_str,
            l["fecha"],
        )

    console.print(tabla)

