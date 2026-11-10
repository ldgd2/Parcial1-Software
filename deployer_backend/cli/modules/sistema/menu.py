import os
import subprocess
from cli.console import console, print_header
from rich.prompt import Prompt

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
SERVICE_DIR = "/etc/systemd/system"
NGINX_CONF_DIR = "/etc/nginx/sites-available"

# En el VPS conviven dos proyectos. Puertos:
#   diagramador: backend 127.0.0.1:8000 · nginx 80 (dominio) / 80 + 8080 (IP)
#   deployer:    uvicorn 127.0.0.1:8001  · nginx 80 con su subdominio / 8081 (IP)
#   apps desplegadas: desde el 9000 (ver deploy_service.PUERTOS_RESERVADOS)
PUERTO_DEPLOYER = 8001
PUERTO_PUBLICO_IP = 8081


def conf_nginx_deployer(listen: int, server_name: str) -> str:
    return f"""server {{
    listen {listen};
    server_name {server_name};

    # Apps desplegadas (/host/<dueño>/<proyecto>/), las escribe el deployer
    include /etc/nginx/deploy_apps/*.conf;

    location / {{
        proxy_pass http://127.0.0.1:{PUERTO_DEPLOYER}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # compilar/desplegar un proyecto tarda: sin esto nginx corta a los 60 s
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        client_max_body_size 100m;
    }}
}}
"""

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
    # Solo en local: el acceso público pasa por nginx (así no choca con el `listen` de nginx
    # en modo IP, que antes también usaba el 8001).
    comando = f"{BASE_DIR}/venv/bin/uvicorn main:app --host 127.0.0.1 --port {PUERTO_DEPLOYER}"
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
    
    # 2. Nginx: un sitio PROPIO del deployer (no toca los del diagramador)
    os.system("sudo mkdir -p /etc/nginx/deploy_apps && sudo chmod 777 /etc/nginx/deploy_apps")
    if modo == "dominio":
        dominio = Prompt.ask("Ingresa el subdominio para el Deployer (Ej: host.example.com)")
        conf_nginx = conf_nginx_deployer(listen=80, server_name=dominio)
        nombre = "deployer.conf"
        url_publica = f"http(s)://{dominio}"
    else:
        ip = Prompt.ask("Ingresa la IP pública de tu servidor")
        conf_nginx = conf_nginx_deployer(listen=PUERTO_PUBLICO_IP, server_name=ip)
        nombre = "deployer-ip.conf"
        url_publica = f"http://{ip}:{PUERTO_PUBLICO_IP}"
    with open(f"/tmp/{nombre}", "w") as f: f.write(conf_nginx)
    os.system(f"sudo mv /tmp/{nombre} /etc/nginx/sites-available/")
    os.system(f"sudo ln -sf /etc/nginx/sites-available/{nombre} /etc/nginx/sites-enabled/")
    console.print(f"[cyan]Deployer público en {url_publica}  (en el backend del diagramador: DEPLOYER_URL={url_publica.replace('http(s)', 'https')})[/cyan]")

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
