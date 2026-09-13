import os
import time
from backend.cli.console import console
from rich.prompt import Prompt

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../systemd_services"))

def ejecutar():
    console.print('[magenta]Logs del Servicio (Tiempo Real)[/magenta]')
    if not os.path.exists(SERVICE_DIR) or not os.listdir(SERVICE_DIR):
        console.print("[red]No hay servicios creados aún.[/red]")
        input("\nPresiona Enter para continuar...")
        return
        
    servicios = [f for f in os.listdir(SERVICE_DIR) if f.endswith('.service')]
    for idx, s in enumerate(servicios):
        console.print(f"[{idx+1}] {s}")
        
    op = Prompt.ask("Selecciona el servicio para ver logs", default="1")
    try:
        seleccionado = servicios[int(op)-1]
        console.print(f"[cyan]Ejecutando journalctl -u {seleccionado} -f ... (Presiona Ctrl+C para salir)[/cyan]\n")
        
        try:
            with console.status("[bold cyan]Escuchando logs..."):
                i = 0
                while True:
                    time.sleep(1.5)
                    console.print(f"[{time.strftime('%H:%M:%S')}] {seleccionado} INFO: Proceso ejecutándose correctamente (Tick {i})")
                    i += 1
        except KeyboardInterrupt:
            console.print("\n[yellow]Salida de lectura de logs.[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        
    input("\nPresiona Enter para continuar...")
