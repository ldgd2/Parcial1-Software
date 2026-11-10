import os
import time
import re
import subprocess
import tempfile
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
        console.print("[7] Ajustar NGINX (tiempos de espera de la IA)")
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
        elif op == "7":
            ajustar_nginx()
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

    # 2. (Eliminado) Frontend ya no usa Systemd, lo servirá NGINX directamente.

    # 3. Crear NGINX configs
    if modo == "dominio":
        dominio_base = Prompt.ask("Ingresa tu dominio base (ej: example.com)")
        conf_frontend = f"""server {{
    listen 80;
    server_name diagramador.{dominio_base};
    
    root /var/www/diagramador-frontend;
    index index.html;

    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}
"""
        conf_backend = f"""server {{
    listen 80;
    server_name api-diagramador.{dominio_base};

    location / {{
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # La IA (/prompt/generar, /optimizar…) puede tardar más de 60 s: con el valor por defecto
        # nginx corta con 504 sin cabeceras CORS y el navegador solo muestra "Failed to fetch".
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        client_max_body_size 25m;   # imágenes / audio / PDF en base64
    }}
}}
"""
        with open(os.path.join(NGINX_CONF_DIR, "diagramador-dominio-front"), "w") as f: f.write(conf_frontend)
        with open(os.path.join(NGINX_CONF_DIR, "diagramador-dominio-back"), "w") as f: f.write(conf_backend)
    
    else: # modo == "ip"
        ip_address = Prompt.ask("Ingresa la IP pública de tu servidor (ej: 172.x.x.x)")
        conf_ip = f"""# Frontend en puerto 80
server {{
    listen 80;
    server_name {ip_address};

    root /var/www/diagramador-frontend;
    index index.html;

    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}

# Backend en puerto 8080
server {{
    listen 8080;
    server_name {ip_address};

    location / {{
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # La IA (/prompt/generar, /optimizar…) puede tardar más de 60 s: con el valor por defecto
        # nginx corta con 504 sin cabeceras CORS y el navegador solo muestra "Failed to fetch".
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        client_max_body_size 25m;   # imágenes / audio / PDF en base64
    }}
}}
"""
        with open(os.path.join(NGINX_CONF_DIR, "diagramador-ip"), "w") as f: f.write(conf_ip)

    # 4. Habilitar todo (Ejecución real en Ubuntu)
    if os.name != 'nt':
        console.print("[cyan]Configurando entorno de producción para el Frontend...[/cyan]")
        env_prod_path = os.path.join(BASE_DIR, "frontend", ".env.production")
        if modo == "dominio":
            api_url = f"https://api-diagramador.{dominio_base}"
            ws_url = f"wss://api-diagramador.{dominio_base}"
        else:
            api_url = f"http://{ip_address}:8080"
            ws_url = f"ws://{ip_address}:8080"
            
        with open(env_prod_path, "w") as f:
            f.write(f"VITE_API_URL={api_url}\n")
            f.write(f"VITE_HOST_API_URL={ws_url}\n")

        console.print("[cyan]Haciendo build del Frontend...[/cyan]")
        subprocess.run("npm run build", cwd=os.path.join(BASE_DIR, "frontend"), shell=True)
        # Asegurar NGINX instalado y directorios requeridos
        if subprocess.run("which nginx", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
            console.print("[cyan]Instalando NGINX...[/cyan]")
            os.system("sudo apt-get update && sudo apt-get install -y nginx")

        os.system("sudo mkdir -p /var/www /etc/nginx/sites-available /etc/nginx/sites-enabled")
        os.system(f"sudo rm -rf /var/www/diagramador-frontend")
        os.system(f"sudo cp -r {os.path.join(BASE_DIR, 'frontend', 'dist')} /var/www/diagramador-frontend")

        console.print("[cyan]Inicializando esquema de base de datos...[/cyan]")
        os.system(f"{BASE_DIR}/backend/venv/bin/python -c \"import asyncio; import backend.main; from backend.core.database import init_db; asyncio.run(init_db())\" 2>/dev/null || true")
        
        console.print("[cyan]Aplicando configuraciones NGINX y Systemd...[/cyan]")
        os.system(f"sudo cp {SERVICE_DIR}/*.service /etc/systemd/system/")
        os.system("sudo systemctl daemon-reload")
        os.system("sudo systemctl enable --now backend-app")
        
        os.system(f"sudo cp {NGINX_CONF_DIR}/* /etc/nginx/sites-available/")
        if modo == "dominio":
            os.system("sudo ln -sf /etc/nginx/sites-available/diagramador-dominio-front /etc/nginx/sites-enabled/")
            os.system("sudo ln -sf /etc/nginx/sites-available/diagramador-dominio-back /etc/nginx/sites-enabled/")
        else:
            os.system("sudo ln -sf /etc/nginx/sites-available/diagramador-ip /etc/nginx/sites-enabled/")
            
        os.system("sudo nginx -t && sudo systemctl enable --now nginx && sudo systemctl reload nginx")
        console.print("[bold green]✔ Todo Creado e Iniciado Correctamente![/bold green]")
    else:
        console.print("[bold green]✔ Mock de creación (Windows).[/bold green]")


def reiniciar_todo():
    if not existe_servicio(): return console.print("[red]No hay servicios activos.[/red]")
    
    if os.name != 'nt':
        console.print("[cyan]Haciendo rebuild del Frontend...[/cyan]")
        
        # Intentar inferir el dominio/IP de los archivos de NGINX si existen para reconstruir el .env.production
        env_prod_path = os.path.join(BASE_DIR, "frontend", ".env.production")
        if not os.path.exists(env_prod_path):
            console.print("[yellow]No se encontró .env.production, se compilará con las variables por defecto.[/yellow]")
            
        subprocess.run("npm run build", cwd=os.path.join(BASE_DIR, "frontend"), shell=True)
        os.system("sudo mkdir -p /var/www")
        os.system(f"sudo rm -rf /var/www/diagramador-frontend")
        os.system(f"sudo cp -r {os.path.join(BASE_DIR, 'frontend', 'dist')} /var/www/diagramador-frontend")
        
        # Servidores creados antes de este ajuste: se les agregan los tiempos de espera de la IA
        ajustar_nginx(recargar=False)

        console.print("[cyan]Reiniciando servicios...[/cyan]")
        os.system("sudo systemctl restart backend-app nginx")
        console.print("[bold green]✔ Servicios reiniciados.[/bold green]")
    else:
        console.print("[bold green]✔ Mock de reinicio (Windows).[/bold green]")

def detener_todo():
    if not existe_servicio(): return console.print("[red]No hay servicios activos.[/red]")
    if os.name != 'nt':
        console.print("[cyan]Deteniendo servicios...[/cyan]")
        os.system("sudo systemctl stop backend-app")
        console.print("[bold green]✔ Servicios detenidos.[/bold green]")
    else:
        console.print("[bold green]✔ Mock de detención (Windows).[/bold green]")

def eliminar_todo():
    if not existe_servicio(): return console.print("[red]No hay servicios activos.[/red]")
    confirm = Prompt.ask("¿Estás seguro de eliminar TODOS los servicios y configuraciones?", choices=["s", "n"], default="n")
    if confirm == 's':
        if os.name != 'nt':
            console.print("[cyan]Eliminando servicios Systemd...[/cyan]")
            os.system("sudo systemctl stop backend-app frontend-app 2>/dev/null")
            os.system("sudo systemctl disable backend-app frontend-app 2>/dev/null")
            os.system("sudo rm -f /etc/systemd/system/backend-app.service /etc/systemd/system/frontend-app.service")
            os.system("sudo systemctl daemon-reload")
            
            console.print("[cyan]Eliminando configuraciones NGINX...[/cyan]")
            os.system("sudo rm -f /etc/nginx/sites-enabled/diagramador-dominio-front /etc/nginx/sites-enabled/diagramador-dominio-back /etc/nginx/sites-enabled/diagramador-ip")
            os.system("sudo rm -f /etc/nginx/sites-available/diagramador-dominio-front /etc/nginx/sites-available/diagramador-dominio-back /etc/nginx/sites-available/diagramador-ip")
            os.system("sudo nginx -t && sudo systemctl enable --now nginx && sudo systemctl reload nginx")
            
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
        console.print("\n[bold cyan]--- ESTADO FRONTEND (Estático NGINX) ---[/bold cyan]")
        if os.path.exists("/var/www/diagramador-frontend"):
            console.print("[green]Archivos compilados disponibles en /var/www/diagramador-frontend[/green]")
        else:
            console.print("[red]Directorio /var/www/diagramador-frontend no encontrado[/red]")
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
        console.print("[2] Ver log de Nginx (Accesos Frontend)")
        console.print("[3] Ver log de Nginx (Errores)")
        console.print("[0] Volver")
        op = Prompt.ask("Selecciona", default="1")
        
        if op == "1" and os.name != 'nt':
            os.system("sudo journalctl -u backend-app -f")
        elif op == "2" and os.name != 'nt':
            os.system("sudo tail -f /var/log/nginx/access.log")
        elif op == "3" and os.name != 'nt':
            os.system("sudo tail -f /var/log/nginx/error.log")
        elif op == "0":
            break
        else:
            if os.name == 'nt': console.print("[bold green]✔ Mock logs (Windows).[/bold green]")


# ─── Ajuste de NGINX para la IA ──────────────────────────────────────────────
# Con los valores por defecto nginx corta a los 60 s: una petición larga a la IA (p. ej.
# "@diag /optimizar todo el diagrama") recibe 504 sin cabeceras CORS y el navegador solo
# muestra "Failed to fetch". También limita el cuerpo a 1 MB (imágenes/audio/PDF en base64).
AJUSTES_NGINX_BACKEND = {
    "proxy_read_timeout": "300s",
    "proxy_send_timeout": "300s",
    "client_max_body_size": "25m",
}
ARCHIVOS_NGINX_BACKEND = ("diagramador-dominio-back", "diagramador-ip")


def _ajustar_texto_nginx(texto: str):
    """Agrega/actualiza los ajustes en cada `location` que hace proxy al backend (:8000).
    Devuelve (texto_nuevo, cantidad_de_cambios). Es idempotente."""
    cambios = 0

    def ajustar_bloque(m):
        nonlocal cambios
        cabecera, cuerpo, cierre = m.group(1), m.group(2), m.group(3)
        if ":8000" not in cuerpo:
            return m.group(0)
        sangria = (re.search(r"\n([ \t]+)proxy_pass", cuerpo) or re.search(r"\n([ \t]+)\S", cuerpo))
        sangria = sangria.group(1) if sangria else "        "
        for clave, valor in AJUSTES_NGINX_BACKEND.items():
            patron = re.compile(rf"^([ \t]*){clave}\s+([^;]+);", re.M)
            actual = patron.search(cuerpo)
            if actual:
                if actual.group(2).strip() != valor:
                    cuerpo = patron.sub(lambda a: f"{a.group(1)}{clave} {valor};", cuerpo, count=1)
                    cambios += 1
            else:
                cuerpo = cuerpo.rstrip() + f"\n{sangria}{clave} {valor};"
                cambios += 1
        return cabecera + cuerpo + cierre

    nuevo = re.sub(r"(location\s+[^{]*\{)([^{}]*?)(\n[ \t]*\})", ajustar_bloque, texto)
    return nuevo, cambios


def _ajustar_archivo(ruta: str, con_sudo: bool):
    """Devuelve la ruta del respaldo si cambió el archivo, '' si ya estaba bien, None si no existe."""
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    nuevo, cambios = _ajustar_texto_nginx(texto)
    if not cambios:
        return ""
    respaldo = ruta + ".bak"
    if con_sudo:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".conf") as tmp:
            tmp.write(nuevo)
        os.system(f'sudo cp "{ruta}" "{respaldo}" && sudo cp "{tmp.name}" "{ruta}"')
        os.remove(tmp.name)
    else:
        with open(respaldo, "w", encoding="utf-8") as f: f.write(texto)
        with open(ruta, "w", encoding="utf-8") as f: f.write(nuevo)
    return respaldo


def ajustar_nginx(recargar: bool = True):
    """Aplica AJUSTES_NGINX_BACKEND a las configuraciones ya creadas (locales y de /etc/nginx)."""
    console.print("\n[cyan]⚙️  Ajustando NGINX para respuestas largas de la IA...[/cyan]")
    # Copias locales (las que se vuelven a copiar a /etc/nginx al crear)
    for nombre in ARCHIVOS_NGINX_BACKEND:
        _ajustar_archivo(os.path.join(NGINX_CONF_DIR, nombre), con_sudo=False)

    if os.name == 'nt':
        return console.print("[bold green]✔ Configuraciones locales ajustadas (en Windows no hay NGINX que recargar).[/bold green]")

    respaldos, encontrados = [], 0
    for nombre in ARCHIVOS_NGINX_BACKEND:
        r = _ajustar_archivo(os.path.join("/etc/nginx/sites-available", nombre), con_sudo=True)
        if r is None:
            continue
        encontrados += 1
        if r:
            respaldos.append((os.path.join("/etc/nginx/sites-available", nombre), r))
            console.print(f"[green]  • {nombre}: ajustado (respaldo en {r})[/green]")
        else:
            console.print(f"[green]  • {nombre}: ya estaba ajustado[/green]")

    if not encontrados:
        return console.print("[yellow]No hay configuraciones de NGINX del diagramador. Usa 'Crear e Iniciar TODO'.[/yellow]")
    if not respaldos:
        return console.print("[bold green]✔ NGINX ya tenía los tiempos de espera correctos.[/bold green]")

    if os.system("sudo nginx -t") != 0:
        console.print("[bold red]❌ La configuración nueva no es válida: se restauran los respaldos.[/bold red]")
        for ruta, respaldo in respaldos:
            os.system(f'sudo cp "{respaldo}" "{ruta}"')
        return
    if recargar:
        os.system("sudo systemctl reload nginx")
    console.print("[bold green]✔ NGINX ajustado: la IA tiene hasta 300 s y se aceptan archivos de hasta 25 MB.[/bold green]")

