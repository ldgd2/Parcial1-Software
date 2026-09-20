#!/bin/bash

# Script de instalación automática para el Deployer Backend
# (Instala entorno y configura Nginx + SystemD)

echo "==================================================="
echo " 🚀 AUTOMATED SETUP PARA DEPLOYER BACKEND "
echo "==================================================="

# 1. Dependencias del sistema (igual que setup-diag)
echo -e "\n[1/4] Verificando dependencias del sistema..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip nginx sqlite3 postgresql postgresql-contrib openjdk-17-jdk maven
    # Asegurar que JAVA_HOME apunta a JDK 17
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
    sudo update-alternatives --set java /usr/lib/jvm/java-17-openjdk-amd64/bin/java 2>/dev/null || true
else
    echo "Sistema no Linux detectado. Se omiten instalaciones apt-get."
fi

# 2. Setup del entorno Python
echo -e "\n[2/4] Configurando el entorno Python para el Deployer..."
cd deployer_backend

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

PROJECT_ROOT=$(pwd)

# Prompt for the deployer domain
read -p "Ingresa el subdominio de este VPS (ej. host.example.com) [host.example.com]: " DEPLOYER_DOMAIN
DEPLOYER_DOMAIN=${DEPLOYER_DOMAIN:-host.example.com}

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # -- NGINX --
    if [ ! -f "/etc/nginx/sites-available/deployer" ]; then
        echo "Creando configuración Nginx para Deployer en $DEPLOYER_DOMAIN..."
        sudo bash -c "mkdir -p /etc/nginx/deploy_apps
chmod 777 /etc/nginx/deploy_apps

# Asegurar que deploy_apps está incluido en nginx.conf
if ! grep -q \"include /etc/nginx/deploy_apps/\\*.conf;\" /etc/nginx/nginx.conf; then
    sed -i '/include \\/etc\\/nginx\\/conf\\.d\\/\\*\\.conf;/a \\ \\ \\ \\ include /etc/nginx/deploy_apps/*.conf;' /etc/nginx/nginx.conf
fi

cat <<EOF > /etc/nginx/sites-available/gerlextech
server {
    listen 80;
    server_name $DOMAIN_NAME;

    # Frontend estático
    location / {
        root $CURRENT_DIR/frontend/dist;
        index index.html;
        try_files \\\$uri \\\$uri/ /index.html;
    }

    # API principal
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
    }

    # API Deployer
    location /deploy-api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
    }
}
EOF"
        sudo ln -sf /etc/nginx/sites-available/gerlextech /etc/nginx/sites-enabled/
        sudo nginx -t && sudo systemctl reload nginx
    else
        echo "La configuración de Nginx (deployer) ya existe."
    fi

    # -- SYSTEMD --
    if [ ! -f "/etc/systemd/system/deployer-backend.service" ]; then
        echo "Creando servicio SystemD para Deployer..."
        sudo bash -c "cat <<EOF > /etc/systemd/system/deployer-backend.service
[Unit]
Description=Deployer Backend (FastAPI)
After=network.target

[Service]
User=\$USER
WorkingDirectory=${PROJECT_ROOT}
Environment=\"PATH=${PROJECT_ROOT}/venv/bin\"
# main.py levanta el servidor, o uvicorn directamente:
ExecStart=${PROJECT_ROOT}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
EOF"
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
echo "   cd deployer_backend"
echo "   python manager.py"
echo "==================================================="
