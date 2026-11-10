#!/usr/bin/env bash
# Script de instalación automática para el Deployer Backend
# (Instala entorno y configura Nginx + SystemD)
#
# Uso:  bash setup-deploy.sh   (o ./setup-deploy.sh). Si se lanza con `sh`, se relanza con bash:
# en Ubuntu `sh` es dash, que no entiende [[ ]], `echo -e` ni `source`.
if [ -z "$BASH_VERSION" ]; then
    exec bash "$0" "$@"
fi
set -e

# Rutas absolutas: funciona igual desde la raíz del repo o desde deployer_backend/
DEPLOYER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$DEPLOYER_DIR")"
ES_LINUX=false
[[ "$(uname -s)" == "Linux" ]] && ES_LINUX=true

echo "==================================================="
echo " 🚀 AUTOMATED SETUP PARA DEPLOYER BACKEND "
echo "==================================================="

# 1. Dependencias del sistema (igual que setup-diag)
echo -e "\n[1/4] Verificando dependencias del sistema..."
if $ES_LINUX; then
    # En un VPS recién creado `unattended-upgrades` suele tener tomado el candado de dpkg unos
    # minutos: se espera (hasta 15 min) en vez de fallar con "Could not get lock".
    APT="sudo apt-get -o DPkg::Lock::Timeout=900"
    if pgrep -f unattended-upgrade > /dev/null; then
        echo "⏳ Ubuntu está instalando actualizaciones automáticas (bloquean apt)."
        read -r -p "   ¿Detenerlas ahora para continuar ya? Terminan el paquete en curso y se reanudan solas otro día [S/n]: " DETENER
        if [[ ! "$DETENER" =~ ^[nN] ]]; then
            # Parada ordenada: unattended-upgrades termina el paquete que está instalando y sale
            sudo systemctl stop unattended-upgrades 2>/dev/null || true
            sudo systemctl stop apt-daily.service apt-daily-upgrade.service 2>/dev/null || true
            for _ in $(seq 1 60); do pgrep -f unattended-upgrade > /dev/null || break; sleep 2; done
            sudo dpkg --configure -a   # deja dpkg consistente si quedó algo a medias
        else
            echo "   Se espera a que terminen (máximo 15 min; sigue apenas se libere apt)."
        fi
    fi
    $APT update
    $APT install -y python3 python3-venv python3-pip python3-dev build-essential nginx sqlite3 postgresql postgresql-contrib openjdk-17-jdk maven
    # Asegurar que JAVA_HOME apunta a JDK 17
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
    sudo update-alternatives --set java /usr/lib/jvm/java-17-openjdk-amd64/bin/java 2>/dev/null || true
else
    echo "Sistema no Linux detectado. Se omiten instalaciones apt-get."
fi

# 2. Setup del entorno Python
echo -e "\n[2/4] Configurando el entorno Python para el Deployer..."
cd "$DEPLOYER_DIR"

if [ ! -d "venv" ]; then
    echo "Creando entorno virtual (venv)..."
    python3 -m venv venv || python -m venv venv
else
    echo "El entorno virtual ya existe."
fi

echo "Instalando dependencias de Python..."
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

# Configurar .env si aplica (puedes ajustar esto si usa postgres)
if [ ! -f ".env" ]; then
    echo "Creando archivo .env por defecto para Deployer..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        echo "API_V1_STR=/api/v1" > .env
        echo "PROJECT_NAME=\"Deployer API\"" >> .env
        echo "DATABASE_URL=sqlite+aiosqlite:///./deployer.db" >> .env
    fi
fi

# 3. Configuración Nginx y SystemD
echo -e "\n[3/4] Configurando Nginx y SystemD..."

read -r -p "Ingresa el subdominio de este VPS (ej. host.example.com) [host.example.com]: " DEPLOYER_DOMAIN
DEPLOYER_DOMAIN=${DEPLOYER_DOMAIN:-host.example.com}

if $ES_LINUX; then
    # -- NGINX --
    # Sitio PROPIO del deployer (mismo archivo que crea `python manager.py` → Sistema → Dominio).
    # Solo su subdominio → uvicorn 127.0.0.1:8001 + apps desplegadas. El diagramador tiene sus
    # propios sitios (diagramador-dominio-*), así que los dos proyectos no se pisan.
    NGINX_SITE=/etc/nginx/sites-available/deployer.conf

    # Versión anterior de este script: creaba "gerlextech" mezclando el frontend y la API del
    # diagramador (puerto 8000) dentro del sitio del deployer.
    if [ -f /etc/nginx/sites-available/gerlextech ] && grep -q "deploy-api" /etc/nginx/sites-available/gerlextech; then
        echo "Quitando el sitio 'gerlextech' de la versión anterior (mezclaba ambos proyectos)..."
        sudo rm -f /etc/nginx/sites-enabled/gerlextech /etc/nginx/sites-available/gerlextech
    fi
    # Las apps escriben bloques `location`: van DENTRO del server del deployer, nunca en nginx.conf
    sudo sed -i '\|^[[:space:]]*include /etc/nginx/deploy_apps/\*\.conf;|d' /etc/nginx/nginx.conf

    if [ ! -f "$NGINX_SITE" ]; then
        echo "Creando configuración Nginx para el Deployer en $DEPLOYER_DOMAIN..."
        sudo mkdir -p /etc/nginx/deploy_apps
        sudo chmod 777 /etc/nginx/deploy_apps

        TMP_CONF="$(mktemp)"
        # 'EOF' entre comillas: las variables de nginx ($host…) quedan literales
        cat > "$TMP_CONF" <<'EOF'
server {
    listen 80;
    server_name __DOMINIO__;

    # Apps desplegadas (/host/<dueño>/<proyecto>/), las escribe el deployer
    include /etc/nginx/deploy_apps/*.conf;

    location / {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # compilar/desplegar un proyecto tarda: sin esto nginx corta a los 60 s
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        client_max_body_size 100m;
    }
}
EOF
        sed -i "s|__DOMINIO__|${DEPLOYER_DOMAIN}|" "$TMP_CONF"
        sudo cp "$TMP_CONF" "$NGINX_SITE"
        rm -f "$TMP_CONF"
        sudo ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/
    else
        echo "La configuración de Nginx ($NGINX_SITE) ya existe."
    fi
    sudo nginx -t && sudo systemctl reload nginx

    # -- SYSTEMD --
    if [ ! -f "/etc/systemd/system/deployer-backend.service" ]; then
        echo "Creando servicio SystemD para Deployer..."
        sudo tee /etc/systemd/system/deployer-backend.service > /dev/null <<EOF
[Unit]
Description=Deployer Backend (FastAPI)
After=network.target

[Service]
User=root
WorkingDirectory=${DEPLOYER_DIR}
Environment="PATH=${DEPLOYER_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${DEPLOYER_DIR}/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        sudo systemctl enable deployer-backend.service
        sudo systemctl start deployer-backend.service
    else
        echo "El servicio SystemD (deployer-backend.service) ya existe."
    fi
else
    echo "⚠️ Omitiendo Nginx y SystemD (Solo soportado en Linux nativo)."
fi

# 4. Finalizado
echo -e "\n==================================================="
echo " 🎉 ¡SETUP DEPLOYER COMPLETADO! 🎉"
echo "==================================================="
echo "💻 PARA EJECUTAR MANUALMENTE:"
echo "   cd $DEPLOYER_DIR"
echo "   python manager.py"
echo "==================================================="
