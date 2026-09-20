import os
import subprocess
from cli.console import console, print_header
from rich.prompt import Prompt

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
SERVICE_DIR = "/etc/systemd/system"
NGINX_CONF_DIR = "/etc/nginx/sites-available"

def menu_sistema():
    while True:
        print_header("Gestión de Sistema y Despliegue (Deployer)")
        
        console.print("[1] Configurar Deployer por Dominio (Ej. deploy.tusitio.com)")
        console.print("[2] Configurar Deployer por IP (Directo al VPS)")
        console.print("[3] Detener y Eliminar Servicios del Deployer")
        console.print("[4] Ver Estado del Servicio Deployer")
        console.print("[5] Ver Logs del Deployer en Tiempo Real (journalctl)")
        console.print("[6] Ver Logs de Errores Nginx")
        console.print("[7] Reiniciar Servicio Deployer")
        console.print("[0] Volver")
        
        op = Prompt.ask("\nSelecciona una opción", default="0")
        
        if op == "1":
            crear_servicios(modo="dominio")
        elif op == "2":
            crear_servicios(modo="ip")
        elif op == "3":
            eliminar_servicios()
        elif op == "4":
            if os.name != 'nt':
                os.system("sudo systemctl status deployer-backend")
                input("\nPresiona Enter para continuar...")
        elif op == "5":
            if os.name != 'nt':
                console.print("[cyan]Mostrando logs en tiempo real. Presiona Ctrl+C para salir.[/cyan]")
                try:
                    os.system("sudo journalctl -u deployer-backend -f -n 50")
                except KeyboardInterrupt:
                    pass
        elif op == "6":
            if os.name != 'nt':
                console.print("[cyan]Mostrando últimos 50 errores de Nginx. Presiona Ctrl+C para salir.[/cyan]")
                try:
                    os.system("sudo tail -f -n 50 /var/log/nginx/error.log")
                except KeyboardInterrupt:
                    pass
        elif op == "7":
            if os.name != 'nt':
                console.print("[cyan]Reiniciando Deployer...[/cyan]")
                os.system("sudo systemctl restart deployer-backend")
                console.print("[bold green]✔ Servicio reiniciado.[/bold green]")
                input("\nPresiona Enter para continuar...")
        elif op == "0":
            break

def crear_servicios(modo):
    if os.name == 'nt':
        console.print("[yellow]Estas configuraciones solo aplican en entornos Linux.[/yellow]")
        input("Presiona Enter...")
        return
        
    console.print("\n[cyan]⚙️  Generando servicios y configuraciones...[/cyan]")
    
    # 1. Systemd
    comando = f"{BASE_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001"
    content_service = f"""[Unit]
Description=Deployer Backend API
After=network.target

[Service]
User=root
WorkingDirectory={BASE_DIR}
ExecStart={comando}
Restart=always

[Install]
WantedBy=multi-user.target
"""
    with open("/tmp/deployer-backend.service", "w") as f: f.write(content_service)
    os.system("sudo mv /tmp/deployer-backend.service /etc/systemd/system/")
    
    # 2. Nginx
    if modo == "dominio":
        dominio = Prompt.ask("Ingresa el subdominio para el Deployer (Ej: deploy.gerlextech.com)")
        conf_nginx = f"""server {{
    listen 80;
    server_name {dominio};

    location / {{
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
        with open("/tmp/deployer.conf", "w") as f: f.write(conf_nginx)
        os.system("sudo mv /tmp/deployer.conf /etc/nginx/sites-available/")
        os.system("sudo ln -sf /etc/nginx/sites-available/deployer.conf /etc/nginx/sites-enabled/")
    else:
        ip = Prompt.ask("Ingresa la IP pública de tu servidor")
        conf_nginx = f"""server {{
    listen 8001;
    server_name {ip};

    location / {{
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""
        with open("/tmp/deployer-ip.conf", "w") as f: f.write(conf_nginx)
        os.system("sudo mv /tmp/deployer-ip.conf /etc/nginx/sites-available/")
        os.system("sudo ln -sf /etc/nginx/sites-available/deployer-ip.conf /etc/nginx/sites-enabled/")

    # Enable and start
    console.print("[cyan]Habilitando servicios...[/cyan]")
    os.system("sudo systemctl daemon-reload")
    os.system("sudo systemctl enable --now deployer-backend")
    os.system("sudo nginx -t && sudo systemctl reload nginx")
    console.print("[bold green]✔ Deployer configurado y corriendo.[/bold green]")
    input("Presiona Enter para continuar...")

def eliminar_servicios():
    if os.name == 'nt': return
    console.print("[cyan]Eliminando servicios del Deployer...[/cyan]")
    os.system("sudo systemctl stop deployer-backend")
    os.system("sudo systemctl disable deployer-backend")
    os.system("sudo rm -f /etc/systemd/system/deployer-backend.service")
    os.system("sudo systemctl daemon-reload")
    
    os.system("sudo rm -f /etc/nginx/sites-enabled/deployer.conf /etc/nginx/sites-enabled/deployer-ip.conf")
    os.system("sudo rm -f /etc/nginx/sites-available/deployer.conf /etc/nginx/sites-available/deployer-ip.conf")
    os.system("sudo nginx -t && sudo systemctl reload nginx")
    console.print("[bold green]✔ Servicios eliminados.[/bold green]")
    input("Presiona Enter para continuar...")
