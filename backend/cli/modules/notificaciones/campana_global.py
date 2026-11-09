import asyncio
from rich.prompt import Prompt, Confirm
from rich.table import Table
from backend.cli.console import console
from backend.modules.gestion_asistencia_ia.notificaciones.firebase_init import send_fcm_message
from .db_executor import (
    obtener_todos_los_tokens_unicos,
    crear_campana_in_app_todos,
    registrar_log_envio,
)


def ejecutar() -> None:
    console.print("\n[bold cyan]=== LANZAR CAMPANA GLOBAL (A TODOS LOS USUARIOS) ===[/bold cyan]\n")
    console.print("[dim]Esta accion enviara la notificacion tanto a la campana web (In-App) como a los telefonos moviles (Push FCM) de todos los usuarios registrados.[/dim]\n")

    titulo = Prompt.ask("Titulo de la campana", default="Aviso General del Sistema")
    mensaje = Prompt.ask("Mensaje / Contenido", default="Hay novedades importantes en el proyecto.")
    url = Prompt.ask("URL o ruta de destino", default="/dashboard")

    if not Confirm.ask(f"\n[bold yellow]¿Confirmas el lanzamiento de la campana a TODOS?[/bold yellow]", default=True):
        console.print("[dim]Campana cancelada.[/dim]")
        return

    # 1. Crear notificaciones en la base de datos (In-App para todos)
    usuarios_notificados = 0
    with console.status("[bold cyan]Guardando notificacion in-app para todos los usuarios..."):
        try:
            usuarios_notificados = asyncio.run(crear_campana_in_app_todos(
                titulo=titulo,
                mensaje=mensaje,
                url=url,
            ))
            console.print(f"[bold green]In-App:[/bold green] Guardada para {usuarios_notificados} usuarios en la base de datos.")
        except Exception as e:
            console.print(f"[bold red]Error al guardar notificaciones in-app:[/bold red] {e}")

    # 2. Enviar notificaciones push a todos los dispositivos registrados
    tokens = asyncio.run(obtener_todos_los_tokens_unicos())
    exitos_push = 0
    fallos_push = 0

    if not tokens:
        console.print("[yellow]Push FCM: No hay dispositivos moviles registrados para envio push.[/yellow]")
    else:
        console.print(f"\n[cyan]Dispositivos moviles encontrados para Push: {len(tokens)}[/cyan]")
        with console.status("[bold cyan]Enviando Push FCM a todos los dispositivos..."):
            for tok in tokens:
                try:
                    send_fcm_message(
                        token=tok,
                        title=titulo,
                        body=mensaje,
                        data={
                            "tipo": "campana_global",
                            "url": url,
                            "origen": "manager_cli",
                        },
                    )
                    exitos_push += 1
                except Exception as e:
                    fallos_push += 1

    # 3. Resumen final de la campaña
    tabla = Table(title="Resumen de la Campana Global")
    tabla.add_column("Canal", style="cyan")
    tabla.add_column("Destinatarios", justify="right", style="white")
    tabla.add_column("Resultado", justify="center")

    tabla.add_row(
        "Campana Web (In-App)",
        str(usuarios_notificados),
        "[bold green]OK[/bold green]" if usuarios_notificados > 0 else "[yellow]0[/yellow]",
    )
    tabla.add_row(
        "Push Movil (FCM)",
        f"{len(tokens)} disp.",
        f"[bold green]{exitos_push} exitosos[/bold green] / [red]{fallos_push} fallidos[/red]" if tokens else "[dim]-[/dim]",
    )

    console.print("\n")
    console.print(tabla)

