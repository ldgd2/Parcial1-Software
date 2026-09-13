import os
from backend.cli.console import console
from rich.prompt import Prompt

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../systemd_services"))

def ejecutar():
    console.print('[red]Eliminar Servicio Systemd[/red]')
    if not os.path.exists(SERVICE_DIR) or not os.listdir(SERVICE_DIR):
        console.print("[red]No hay servicios creados aún.[/red]")
        input("\nPresiona Enter para continuar...")
        return
        
    servicios = [f for f in os.listdir(SERVICE_DIR) if f.endswith('.service')]
    for idx, s in enumerate(servicios):
        console.print(f"[{idx+1}] {s}")
        
    op = Prompt.ask("Selecciona el servicio a eliminar", default="1")
    try:
        seleccionado = servicios[int(op)-1]
        filepath = os.path.join(SERVICE_DIR, seleccionado)
        
        confirm = Prompt.ask(f"¿Estás seguro de detener y eliminar {seleccionado}?", choices=["s", "n"], default="n")
        if confirm == 's':
            import time
            with console.status(f"[cyan]Ejecutando systemctl stop {seleccionado}...[/cyan]"):
                time.sleep(1)
            with console.status(f"[cyan]Ejecutando systemctl disable {seleccionado}...[/cyan]"):
                time.sleep(1)
                
            os.remove(filepath)
            console.print(f"[bold green]✔ {seleccionado} detenido y eliminado correctamente.[/bold green]")
        else:
            console.print("[yellow]Operación cancelada.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        
    input("\nPresiona Enter para continuar...")
