import os
import time
from backend.cli.console import console
from rich.prompt import Prompt

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../systemd_services"))

def ejecutar():
    console.print('[cyan]Iniciar Servicio Systemd[/cyan]')
    if not os.path.exists(SERVICE_DIR) or not os.listdir(SERVICE_DIR):
        console.print("[red]No hay servicios creados aún.[/red]")
        input("\nPresiona Enter para continuar...")
        return
        
    servicios = [f for f in os.listdir(SERVICE_DIR) if f.endswith('.service')]
    for idx, s in enumerate(servicios):
        console.print(f"[{idx+1}] {s}")
        
    op = Prompt.ask("Selecciona el servicio a iniciar", default="1")
    try:
        seleccionado = servicios[int(op)-1]
        
        with console.status(f"[cyan]Ejecutando systemctl start {seleccionado}...[/cyan]"):
            time.sleep(1)
            
        console.print(f"[bold green]✔ {seleccionado} iniciado correctamente.[/bold green]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        
    input("\nPresiona Enter para continuar...")
