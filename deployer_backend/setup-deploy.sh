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
    if pgrep -x unattended-upgr > /dev/null || pgrep -f unattended-upgrade > /dev/null; then
        echo "⏳ Ubuntu está instalando actualizaciones automáticas; se espera a que termine..."
    fi
    $APT update
    $APT install -y python3 python3-venv python3-pip nginx sqlite3 postgresql postgresql-contrib openjdk-17-jdk maven
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
        echo "MAIN_DB_URL=sqlite+aiosqlite:///./deployer.db" >> .env
    fi
fi

# 3. Configuración Nginx y SystemD
echo -e "\n[3/4] Configurando Nginx y SystemD..."

read -r -p "Ingresa el subdominio de este VPS (ej. host.example.com) [host.example.com]: " DEPLOYER_DOMAIN
DEPLOYER_DOMAIN=${DEPLOYER_DOMAIN:-host.example.com}

if $ES_LINUX; then
    # -- NGINX --
    NGINX_SITE=/etc/nginx/sites-available/gerlextech
    if [ ! -f "$NGINX_SITE" ]; then
        echo "Creando configuración Nginx para Deployer en $DEPLOYER_DOMAIN..."
        sudo mkdir -p /etc/nginx/deploy_apps
        sudo chmod 777 /etc/nginx/deploy_apps

        # Asegurar que deploy_apps está incluido en nginx.conf
        if ! grep -q "include /etc/nginx/deploy_apps/\*.conf;" /etc/nginx/nginx.conf; then
            sudo sed -i '/include \/etc\/nginx\/conf\.d\/\*\.conf;/a \ \ \ \ include /etc/nginx/deploy_apps/*.conf;' /etc/nginx/nginx.conf
        fi

        TMP_CONF="$(mktemp)"
        # 'EOF' entre comillas: las variables de nginx ($host, $uri…) quedan literales;
        # las del script se insertan después con sed.
        cat > "$TMP_CONF" <<'EOF'
server {
    listen 80;
    server_name __DOMINIO__;

    # Frontend estático
    location / {
        root __FRONTEND_DIST__;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API principal
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # La IA puede tardar más de 60 s (si nginx corta, el navegador solo ve "Failed to fetch")
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        client_max_body_size 25m;
    }

    # API Deployer
    location /deploy-api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        client_max_body_size 100m;
    }
}
EOF
        sed -i "s|__DOMINIO__|${DEPLOYER_DOMAIN}|; s|__FRONTEND_DIST__|${REPO_ROOT}/frontend/dist|" "$TMP_CONF"
        sudo cp "$TMP_CONF" "$NGINX_SITE"
        rm -f "$TMP_CONF"
        sudo ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/
        sudo nginx -t && sudo systemctl reload nginx
    else
        echo "La configuración de Nginx ($NGINX_SITE) ya existe."
    fi

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
ExecStart=${DEPLOYER_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
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
