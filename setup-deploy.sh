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
    sudo apt-get install -y python3 python3-venv python3-pip nginx sqlite3
else
    echo "⚠️ Sistema no Linux detectado. Se omiten instalaciones apt-get."
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
echo -e "\n[3/4] Configurando Nginx y SystemD (deploy.gerlex.com)..."

PROJECT_ROOT=$(pwd)

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # -- NGINX --
    if [ ! -f "/etc/nginx/sites-available/deployer" ]; then
        echo "Creando configuración Nginx para Deployer..."
        sudo bash -c 'cat <<EOF > /etc/nginx/sites-available/deployer
server {
    listen 80;
    server_name deploy.gerlex.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF'
        sudo ln -sf /etc/nginx/sites-available/deployer /etc/nginx/sites-enabled/
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
