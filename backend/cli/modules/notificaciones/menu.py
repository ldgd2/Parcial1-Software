from rich.prompt import Prompt
from backend.cli.console import console, print_header
from . import (
    campana_global,
    enviar_push,
    listar_tokens,
    ver_historial,
    enviar_inapp,
    verificar_estado,
)


def menu_notificaciones() -> None:
    while True:
        print_header("MODULO: NOTIFICACIONES")
        console.print("[1] Lanzar Campaña Global (Push + In-App a TODOS)")
        console.print("[2] Enviar Notificacion Push Individual (FCM / Movil)")
        console.print("[3] Enviar Notificacion In-App Individual (Campana Web)")
        console.print("[4] Listar Dispositivos y Tokens Registrados")
        console.print("[5] Ver Historial de Envios Push")
        console.print("[6] Verificar Estado de Firebase Admin SDK")
        console.print("[0] Volver")

        op = Prompt.ask("\nSelecciona una opcion", choices=["1", "2", "3", "4", "5", "6", "0"], default="0")

        if op == "1":
            campana_global.ejecutar()
            Prompt.ask("\nPresiona Enter para continuar")
        elif op == "2":
            enviar_push.ejecutar()
            Prompt.ask("\nPresiona Enter para continuar")
        elif op == "3":
            enviar_inapp.ejecutar()
            Prompt.ask("\nPresiona Enter para continuar")
        elif op == "4":
            listar_tokens.ejecutar()
            Prompt.ask("\nPresiona Enter para continuar")
        elif op == "5":
            ver_historial.ejecutar()
            Prompt.ask("\nPresiona Enter para continuar")
        elif op == "6":
            verificar_estado.ejecutar()
            Prompt.ask("\nPresiona Enter para continuar")
        elif op == "0":
            break
