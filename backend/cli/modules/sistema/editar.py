import os
import subprocess
from backend.cli.console import console
from rich.prompt import Prompt

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../systemd_services"))

def ejecutar():
    console.print('[cyan]Editar Servicio Systemd[/cyan]')
    if not os.path.exists(SERVICE_DIR) or not os.listdir(SERVICE_DIR):
        console.print("[red]No hay servicios creados aún.[/red]")
        input("\nPresiona Enter para continuar...")
        return
        
    servicios = [f for f in os.listdir(SERVICE_DIR) if f.endswith('.service')]
    for idx, s in enumerate(servicios):
        console.print(f"[{idx+1}] {s}")
        
    op = Prompt.ask("Selecciona el servicio a editar", default="1")
    try:
        seleccionado = servicios[int(op)-1]
        filepath = os.path.join(SERVICE_DIR, seleccionado)
        
        # Intentar abrir con notepad en Windows
        console.print(f"[cyan]Abriendo {filepath} en el editor...[/cyan]")
        if os.name == 'nt':
            subprocess.Popen(['notepad.exe', filepath])
        else:
            subprocess.Popen(['nano', filepath])
            
        console.print("[green]Archivo abierto. Guarde los cambios en el editor.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        
    input("\nPresiona Enter para continuar...")
