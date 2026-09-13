import os
import time
from backend.cli.console import console
from rich.prompt import Prompt

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../systemd_services"))

def generar_service(nombre, comando, directorio):
    if not os.path.exists(SERVICE_DIR):
        os.makedirs(SERVICE_DIR)
        
    service_content = f"""[Unit]
Description={nombre} Service
After=network.target

[Service]
User=root
WorkingDirectory={directorio}
ExecStart={comando}
Restart=always

[Install]
WantedBy=multi-user.target
"""
    
    filepath = os.path.join(SERVICE_DIR, f"{nombre}.service")
    with console.status(f"[bold green]Generando archivo en {filepath}...[/bold green]"):
        time.sleep(0.5)
        with open(filepath, "w") as f:
            f.write(service_content)
            
    console.print(f'[bold green]✔ Servicio {nombre}.service creado correctamente en {filepath}.[/bold green]')

def ejecutar():
    console.print('[cyan]Configuración de Nuevo Servicio Systemd[/cyan]')
    
    tipo_servicio = Prompt.ask("¿Qué tipo de servicio deseas crear?", choices=["1", "2", "3", "4"], default="1")
    # 1: Backend, 2: Frontend, 3: Ambos, 4: Personalizado
    
    # Path base
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
    
    if tipo_servicio in ["1", "3"]:
        nombre_b = "backend-app"
        # Usar el venv de linux explícitamente en el comando ExecStart
        comando_b = f"{base_dir}/backend/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000"
        generar_service(nombre_b, comando_b, base_dir)
        
    if tipo_servicio in ["2", "3"]:
        nombre_f = "frontend-app"
        # Usar npm
        comando_f = "npm run preview -- --host 0.0.0.0 --port 4173"
        dir_f = os.path.join(base_dir, "frontend")
        generar_service(nombre_f, comando_f, dir_f)
        
    if tipo_servicio == "4":
        nombre = Prompt.ask("Nombre del servicio (ej. mi-servicio)")
        comando = Prompt.ask("Comando de ejecución (ej. /ruta/venv/bin/uvicorn main:app)")
        directorio = Prompt.ask("Directorio de trabajo")
        
        console.print(f"\n[bold]Resumen:[/bold] Nombre: {nombre} | Cmd: {comando} | Dir: {directorio}")
        confirm = Prompt.ask("¿Crear servicio con estos datos?", choices=["s", "n"], default="s")
        if confirm == 's':
            generar_service(nombre, comando, directorio)
            
    console.print("\nPresiona Enter para continuar...")
    input()
