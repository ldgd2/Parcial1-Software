import os
import time
from backend.cli.console import console
from rich.prompt import Prompt
from backend.cli.modules.sistema.crear import generar_service

NGINX_CONF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../nginx_configs"))
SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../systemd_services"))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))

def crear_archivo_nginx(nombre, contenido):
    if not os.path.exists(NGINX_CONF_DIR):
        os.makedirs(NGINX_CONF_DIR)
        
    filepath = os.path.join(NGINX_CONF_DIR, nombre)
    with console.status(f"[bold green]Generando configuración de Nginx en {filepath}...[/bold green]"):
        time.sleep(0.5)
        with open(filepath, "w") as f:
            f.write(contenido)
            
    console.print(f'[bold green]✔ Configuración {nombre} creada correctamente en {filepath}.[/bold green]')

def ejecutar():
    console.print('[cyan]Configurar Nginx y Servicios (Frontend/Backend)[/cyan]')
    
    # Configuración Frontend
    conf_frontend = """server {
    listen 80;
    server_name diagramador.gerlextech.com;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
"""
    if not os.path.exists(os.path.join(NGINX_CONF_DIR, "diagramador")):
        crear_archivo_nginx("diagramador", conf_frontend)
    else:
        console.print("[yellow]! Configuración Nginx Frontend ('diagramador') ya existe. Omitiendo.[/yellow]")

    # Configuración Backend
    conf_backend = """server {
    listen 80;
    server_name api.diagramador.gerlextech.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
"""
    if not os.path.exists(os.path.join(NGINX_CONF_DIR, "api-diagramador")):
        crear_archivo_nginx("api-diagramador", conf_backend)
    else:
        console.print("[yellow]! Configuración Nginx Backend ('api-diagramador') ya existe. Omitiendo.[/yellow]")

    console.print("\n[cyan]Verificando servicios Systemd compatibles...[/cyan]")
    
    # Crear servicio Backend si no existe
    if not os.path.exists(os.path.join(SERVICE_DIR, "backend-app.service")):
        nombre_b = "backend-app"
        comando_b = f"{BASE_DIR}/backend/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000"
        generar_service(nombre_b, comando_b, BASE_DIR)
    else:
        console.print("[yellow]! Servicio Systemd Backend ('backend-app.service') ya existe. Omitiendo.[/yellow]")

    # Crear servicio Frontend si no existe
    if not os.path.exists(os.path.join(SERVICE_DIR, "frontend-app.service")):
        nombre_f = "frontend-app"
        comando_f = "npm run dev -- --host 0.0.0.0 --port 5173" 
        dir_f = os.path.join(BASE_DIR, "frontend")
        generar_service(nombre_f, comando_f, dir_f)
    else:
        console.print("[yellow]! Servicio Systemd Frontend ('frontend-app.service') ya existe. Omitiendo.[/yellow]")

    # Instrucciones para el despliegue real en Ubuntu
    console.print("\n[bold cyan]INSTRUCCIONES DE DESPLIEGUE (Ubuntu):[/bold cyan]")
    console.print("Para aplicar estos cambios en el servidor, ejecuta:")
    console.print(f"1. [bold]sudo cp {NGINX_CONF_DIR}/* /etc/nginx/sites-available/[/bold]")
    console.print("2. [bold]sudo ln -sf /etc/nginx/sites-available/diagramador /etc/nginx/sites-enabled/[/bold]")
    console.print("3. [bold]sudo ln -sf /etc/nginx/sites-available/api-diagramador /etc/nginx/sites-enabled/[/bold]")
    console.print("4. [bold]sudo nginx -t && sudo systemctl reload nginx[/bold]")
    console.print(f"5. [bold]sudo cp {SERVICE_DIR}/*.service /etc/systemd/system/[/bold]")
    console.print("6. [bold]sudo systemctl daemon-reload[/bold]")
    console.print("7. [bold]sudo systemctl enable --now backend-app frontend-app[/bold]")

    console.print("\nPresiona Enter para continuar...")
    input()
