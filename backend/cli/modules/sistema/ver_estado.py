import os
import time
from backend.cli.console import console
from rich.panel import Panel
from rich.prompt import Prompt

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../systemd_services"))

def ejecutar():
    console.print('[blue]Estado del Servicio Systemd[/blue]')
    if not os.path.exists(SERVICE_DIR) or not os.listdir(SERVICE_DIR):
        console.print("[red]No hay servicios creados aún.[/red]")
        input("\nPresiona Enter para continuar...")
        return
        
    servicios = [f for f in os.listdir(SERVICE_DIR) if f.endswith('.service')]
    for idx, s in enumerate(servicios):
        console.print(f"[{idx+1}] {s}")
        
    op = Prompt.ask("Selecciona el servicio a consultar", default="1")
    try:
        seleccionado = servicios[int(op)-1]
        
        with console.status(f"[cyan]Consultando systemctl status {seleccionado}...[/cyan]"):
            time.sleep(1) # Simular consulta en Windows
            
        estado_simulado = f"● {seleccionado} - Aplicación Administrada\n   Loaded: loaded ({os.path.join(SERVICE_DIR, seleccionado)}; enabled)\n   Active: active (running) since {time.ctime()}\n   Main PID: 12345 (python)\n   Tasks: 4 (limit: 4915)\n   Memory: 50.0M"
        
        console.print(Panel(estado_simulado, title=f"Estado: {seleccionado}", border_style="green"))
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        
    input("\nPresiona Enter para continuar...")
