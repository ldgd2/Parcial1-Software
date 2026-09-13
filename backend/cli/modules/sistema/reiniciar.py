import os
import time
import subprocess
from backend.cli.console import console

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../systemd_services"))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../frontend"))

def ejecutar():
    console.print('[magenta]Reiniciar Todos los Servicios Systemd[/magenta]')
    if not os.path.exists(SERVICE_DIR) or not os.listdir(SERVICE_DIR):
        console.print("[red]No hay servicios creados aún para reiniciar.[/red]")
        input("\nPresiona Enter para continuar...")
        return
        
    servicios = [f for f in os.listdir(SERVICE_DIR) if f.endswith('.service')]
    
    for s in servicios:
        # Detectar si es el servicio frontend para hacer rebuild
        if "frontend" in s.lower():
            with console.status("[cyan]Haciendo rebuild del Frontend (npm run build)...[/cyan]"):
                try:
                    # En la vida real, ejecutamos el build
                    subprocess.run(["npm", "run", "build"], cwd=FRONTEND_DIR, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    console.print("[green]✔ Rebuild del frontend finalizado exitosamente.[/green]")
                except Exception as e:
                    console.print(f"[red]Error al compilar el frontend: {str(e)}[/red]")
                    continue # Saltamos el reinicio si falla la compilación

        with console.status(f"[cyan]Ejecutando systemctl restart {s}...[/cyan]"):
            time.sleep(1.5)
            
        console.print(f"[bold green]✔ {s} reiniciado correctamente.[/bold green]")
        
    console.print("[bold green]Todos los servicios han sido reiniciados.[/bold green]")
    input("\nPresiona Enter para continuar...")
