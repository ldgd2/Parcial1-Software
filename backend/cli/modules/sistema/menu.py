import os
from backend.cli.console import console
from rich.panel import Panel
from rich.prompt import Prompt
from backend.cli.modules.sistema.servicios_controller import ejecutar as ejecutar_servicios

def menu_sistema():
    while True:
        console.print(Panel("[bold cyan]Gestión de Sistema y Despliegue[/bold cyan]", border_style="cyan"))
        
        console.print("[1] Servicios por Dominio")
        console.print("[2] Servicios por IP")
        console.print("[0] Volver al Menú Principal")
        
        op = Prompt.ask("Selecciona una opción", default="1")
        
        if op == "1":
            ejecutar_servicios("dominio")
        elif op == "2":
            ejecutar_servicios("ip")
        elif op == "0":
            break
        else:
            console.print("[red]Opción no válida.[/red]")
