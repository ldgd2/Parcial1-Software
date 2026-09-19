import os
import time
import subprocess
from backend.cli.console import console
from rich.prompt import Prompt
from rich.panel import Panel

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
SERVICE_DIR = os.path.join(BASE_DIR, "systemd_services")
NGINX_CONF_DIR = os.path.join(BASE_DIR, "nginx_configs")

def existe_servicio():
    return os.path.exists(os.path.join(SERVICE_DIR, "backend-app.service"))

def ejecutar(modo):
    while True:
        console.print(f"\n[bold magenta]=== GESTIÓN DE SERVICIOS ({'DOMINIO' if modo == 'dominio' else 'IP'}) ===[/bold magenta]")
        console.print("[1] Crear e Iniciar TODO")
        console.print("[2] Reiniciar TODO")
        console.print("[3] Detener TODO")
        console.print("[4] Eliminar TODO")
        console.print("[5] Ver Estado General")
        console.print("[6] Ver Logs")
        console.print("[0] Volver")
        
        op = Prompt.ask("Selecciona una opción", default="1")
        
        if op == "1":
            if existe_servicio():
                console.print("[bold red]❌ Ya existen servicios creados. Debes 'Eliminar TODO' antes de crear unos nuevos.[/bold red]")
                continue
            crear_todo(modo)
        elif op == "2":
            reiniciar_todo()
        elif op == "3":
            detener_todo()
        elif op == "4":
            eliminar_todo()
        elif op == "5":
            ver_estado()
        elif op == "6":
            menu_logs()
        elif op == "0":
            break
        else:
            console.print("[red]Opción no válida.[/red]")

def crear_todo(modo):
    console.print("\n[cyan]⚙️  Generando servicios y configuraciones...[/cyan]")
    
    if not os.path.exists(SERVICE_DIR): os.makedirs(SERVICE_DIR)
    if not os.path.exists(NGINX_CONF_DIR): os.makedirs(NGINX_CONF_DIR)

    # 1. Crear Systemd para Backend
    comando_b = f"{BASE_DIR}/backend/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000"
    content_b = f"""[Unit]
Description=backend-app Service
After=network.target

[Service]
User=root
WorkingDirectory={BASE_DIR}
ExecStart={comando_b}
Restart=always

[Install]
WantedBy=multi-user.target
"""
    with open(os.path.join(SERVICE_DIR, "backend-app.service"), "w") as f: f.write(content_b)

    # 2. Crear Systemd para Frontend
    comando_f = "npm run preview -- --host 0.0.0.0 --port 4173"
    content_f = f"""[Unit]
Description=frontend-app Service
After=network.target

[Service]
User=root
WorkingDirectory={os.path.join(BASE_DIR, "frontend")}
ExecStart={comando_f}
Restart=always

[Install]
WantedBy=multi-user.target
"""
    with open(os.path.join(SERVICE_DIR, "frontend-app.service"), "w") as f: f.write(content_f)

    # 3. Crear NGINX configs
    if modo == "dominio":
        conf_frontend = """server {
    listen 80;
    server_name diagramador.gerlextech.com;

    location / {
        proxy_pass http://localhost:4173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
"""
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
        with open(os.path.join(NGINX_CONF_DIR, "diagramador-dominio-front"), "w") as f: f.write(conf_frontend)
        with open(os.path.join(NGINX_CONF_DIR, "diagramador-dominio-back"), "w") as f: f.write(conf_backend)
    
    else: # modo == "ip"
        ip_address = Prompt.ask("Ingresa la IP pública de tu servidor (ej: 172.x.x.x)")
        conf_ip = f"""# Frontend en puerto 80
server {{
    listen 80;
    server_name {ip_address};

    location / {{
        proxy_pass http://localhost:4173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}

# Backend en puerto 8080
server {{
    listen 8080;
    server_name {ip_address};

    location / {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""
        with open(os.path.join(NGINX_CONF_DIR, "diagramador-ip"), "w") as f: f.write(conf_ip)

    # 4. Habilitar todo (Ejecución real en Ubuntu)
    if os.name != 'nt':
        console.print("[cyan]Haciendo build del Frontend...[/cyan]")
        subprocess.run("npm run build", cwd=os.path.join(BASE_DIR, "frontend"), shell=True)
        
        console.print("[cyan]Aplicando configuraciones NGINX y Systemd...[/cyan]")
        os.system(f"sudo cp {SERVICE_DIR}/*.service /etc/systemd/system/")
        os.system("sudo systemctl daemon-reload")
        os.system("sudo systemctl enable --now backend-app frontend-app")
        
        os.system(f"sudo cp {NGINX_CONF_DIR}/* /etc/nginx/sites-available/")
        if modo == "dominio":
            os.system("sudo ln -sf /etc/nginx/sites-available/diagramador-dominio-front /etc/nginx/sites-enabled/")
            os.system("sudo ln -sf /etc/nginx/sites-available/diagramador-dominio-back /etc/nginx/sites-enabled/")
        else:
            os.system("sudo ln -sf /etc/nginx/sites-available/diagramador-ip /etc/nginx/sites-enabled/")
            
        os.system("sudo nginx -t && sudo systemctl reload nginx")
        console.print("[bold green]✔ Todo Creado e Iniciado Correctamente![/bold green]")
    else:
        console.print("[bold green]✔ Mock de creación (Windows).[/bold green]")


def reiniciar_todo():
    if not existe_servicio(): return console.print("[red]No hay servicios activos.[/red]")
    
    if os.name != 'nt':
        console.print("[cyan]Haciendo rebuild del Frontend...[/cyan]")
        subprocess.run("npm run build", cwd=os.path.join(BASE_DIR, "frontend"), shell=True)
        console.print("[cyan]Reiniciando servicios...[/cyan]")
        os.system("sudo systemctl restart backend-app frontend-app nginx")
        console.print("[bold green]✔ Servicios reiniciados.[/bold green]")
    else:
        console.print("[bold green]✔ Mock de reinicio (Windows).[/bold green]")

def detener_todo():
    if not existe_servicio(): return console.print("[red]No hay servicios activos.[/red]")
    if os.name != 'nt':
        console.print("[cyan]Deteniendo servicios...[/cyan]")
        os.system("sudo systemctl stop backend-app frontend-app")
        console.print("[bold green]✔ Servicios detenidos.[/bold green]")
    else:
        console.print("[bold green]✔ Mock de detención (Windows).[/bold green]")

def eliminar_todo():
    if not existe_servicio(): return console.print("[red]No hay servicios activos.[/red]")
    confirm = Prompt.ask("¿Estás seguro de eliminar TODOS los servicios y configuraciones?", choices=["s", "n"], default="n")
    if confirm == 's':
        if os.name != 'nt':
            console.print("[cyan]Eliminando servicios Systemd...[/cyan]")
            os.system("sudo systemctl stop backend-app frontend-app")
            os.system("sudo systemctl disable backend-app frontend-app")
            os.system("sudo rm -f /etc/systemd/system/backend-app.service /etc/systemd/system/frontend-app.service")
            os.system("sudo systemctl daemon-reload")
            
            console.print("[cyan]Eliminando configuraciones NGINX...[/cyan]")
            os.system("sudo rm -f /etc/nginx/sites-enabled/diagramador-dominio-front /etc/nginx/sites-enabled/diagramador-dominio-back /etc/nginx/sites-enabled/diagramador-ip")
            os.system("sudo rm -f /etc/nginx/sites-available/diagramador-dominio-front /etc/nginx/sites-available/diagramador-dominio-back /etc/nginx/sites-available/diagramador-ip")
            os.system("sudo nginx -t && sudo systemctl reload nginx")
            
        # Limpieza local
        if os.name != 'nt':
            os.system(f"rm -f {SERVICE_DIR}/*.service")
            os.system(f"rm -f {NGINX_CONF_DIR}/*")
        else:
            # En windows
            import glob
            for f in glob.glob(f"{SERVICE_DIR}/*.service"): os.remove(f)
            for f in glob.glob(f"{NGINX_CONF_DIR}/*"): os.remove(f)
            
        console.print("[bold green]✔ Todo eliminado correctamente. Ahora puedes crear en otro modo.[/bold green]")

def ver_estado():
    if not existe_servicio(): return console.print("[red]No hay servicios activos.[/red]")
    if os.name != 'nt':
        console.print("\n[bold cyan]--- ESTADO BACKEND ---[/bold cyan]")
        os.system("sudo systemctl status backend-app --no-pager")
        console.print("\n[bold cyan]--- ESTADO FRONTEND ---[/bold cyan]")
        os.system("sudo systemctl status frontend-app --no-pager")
        console.print("\n[bold cyan]--- ESTADO NGINX ---[/bold cyan]")
        os.system("sudo systemctl status nginx --no-pager")
    else:
        console.print("[bold green]✔ Mock de estado (Windows).[/bold green]")
    input("\nPresiona Enter para continuar...")

def menu_logs():
    if not existe_servicio(): return console.print("[red]No hay servicios activos.[/red]")
    while True:
        console.print("\n[magenta]--- VER LOGS ---[/magenta]")
        console.print("[1] Ver log del Backend")
        console.print("[2] Ver log del Frontend")
        console.print("[3] Ver log de Nginx (Errores)")
        console.print("[0] Volver")
        op = Prompt.ask("Selecciona", default="1")
        
        if op == "1" and os.name != 'nt':
            os.system("sudo journalctl -u backend-app -f")
        elif op == "2" and os.name != 'nt':
            os.system("sudo journalctl -u frontend-app -f")
        elif op == "3" and os.name != 'nt':
            os.system("sudo tail -f /var/log/nginx/error.log")
        elif op == "0":
            break
        else:
            if os.name == 'nt': console.print("[bold green]✔ Mock logs (Windows).[/bold green]")
