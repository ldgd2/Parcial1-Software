from rich.prompt import Prompt
from backend.cli.console import console
from backend.cli.async_runner import ejecutar_async
from .db_executor import crear_notificacion_in_app


def ejecutar() -> None:
    console.print("\n[bold cyan]=== ENVIAR NOTIFICACION IN-APP (CAMPANA WEB) ===[/bold cyan]\n")

    uid_str = Prompt.ask("ID del usuario destinatario")
    try:
        uid = int(uid_str)
    except ValueError:
        console.print("[bold red]ID invalido.[/bold red]")
        return

    titulo = Prompt.ask("Titulo", default="Aviso del Sistema")
    mensaje = Prompt.ask("Mensaje", default="Mensaje de prueba generado desde el Manager CLI")
    url = Prompt.ask("URL de destino", default="/dashboard")

    try:
        ejecutar_async(crear_notificacion_in_app(
            usuario_id=uid,
            titulo=titulo,
            mensaje=mensaje,
            url=url,
        ))
        console.print("[bold green]Notificacion in-app creada con exito en la base de datos.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error al guardar la notificacion:[/bold red] {e}")

