from rich.prompt import Prompt
from backend.cli.console import console
from backend.cli.async_runner import ejecutar_async
from backend.modules.gestion_notificaciones.firebase_init import send_fcm_message
from .db_executor import (
    obtener_token_por_usuario,
    obtener_todos_los_tokens_unicos,
    registrar_log_envio,
)


def ejecutar() -> None:
    console.print("\n[bold cyan]=== ENVIAR NOTIFICACION PUSH (FCM) ===[/bold cyan]\n")
    console.print("[1] Campaña Broadcast (Enviar a TODOS los dispositivos registrados)")
    console.print("[2] Enviar a Usuario especifico (por ID)")
    console.print("[3] Enviar a Token FCM directo")
    console.print("[0] Cancelar")

    op = Prompt.ask("\nSelecciona el modo de envio", choices=["1", "2", "3", "0"], default="1")
    if op == "0":
        return

    titulo = Prompt.ask("Titulo de la notificacion", default="Campana del Sistema")
    cuerpo = Prompt.ask("Cuerpo del mensaje", default="Aviso general para todos los colaboradores")

    if op == "1":
        tokens = ejecutar_async(obtener_todos_los_tokens_unicos())
        if not tokens:
            console.print("[bold red]No hay dispositivos registrados en la base de datos para enviar la campana.[/bold red]")
            return

        console.print(f"\n[cyan]Dispositivos encontrados para la campana: {len(tokens)}[/cyan]")
        exitos = 0
        fallos = 0

        with console.status("[bold cyan]Enviando notificaciones a todos los dispositivos..."):
            for tok in tokens:
                try:
                    send_fcm_message(
                        token=tok,
                        title=titulo,
                        body=cuerpo,
                        data={"tipo": "campana_broadcast", "origen": "manager_cli"},
                    )
                    exitos += 1
                except Exception as e:
                    fallos += 1
                    console.print(f"[dim red]Error en token {tok[:20]}...: {e}[/dim red]")

        console.print(f"\n[bold green]Campana finalizada:[/bold green] {exitos} exitosos, {fallos} fallidos de {len(tokens)} totales.")
        return

    token_destino = ""
    usuario_id_log = 0

    if op == "2":
        uid_str = Prompt.ask("Ingresa el ID del usuario")
        try:
            uid = int(uid_str)
            usuario_id_log = uid
        except ValueError:
            console.print("[bold red]ID invalido.[/bold red]")
            return

        token_destino = ejecutar_async(obtener_token_por_usuario(uid)) or ""
        if not token_destino:
            console.print(f"[bold red]No se encontro ningun token de dispositivo para el usuario {uid}.[/bold red]")
            return
        console.print(f"[dim]Token encontrado: {token_destino[:25]}...[/dim]")

    elif op == "3":
        token_destino = Prompt.ask("Pega el Device Token de Firebase").strip()
        if not token_destino:
            console.print("[bold red]El token no puede estar vacio.[/bold red]")
            return

    console.print("\n[dim]Enviando mensaje via Firebase Cloud Messaging...[/dim]")

    try:
        msg_id = send_fcm_message(
            token=token_destino,
            title=titulo,
            body=cuerpo,
            data={"tipo": "prueba_cli", "origen": "manager"},
        )
        console.print(f"[bold green]Notificacion enviada con exito.[/bold green]")
        console.print(f"[dim]Firebase Message ID: {msg_id}[/dim]")

        if usuario_id_log > 0:
            ejecutar_async(registrar_log_envio(usuario_id_log, titulo, cuerpo, True, {"msg_id": msg_id}))

    except Exception as e:
        console.print(f"[bold red]Error al enviar la notificacion:[/bold red] {e}")
        if usuario_id_log > 0:
            ejecutar_async(registrar_log_envio(usuario_id_log, titulo, cuerpo, False, {"error": str(e)}))
