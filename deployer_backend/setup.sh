#!/bin/bash

# ==========================================
# SETUP INTERACTIVO - DEPLOYER BACKEND
# ==========================================
# Este script está diseñado para Ubuntu/Debian

set -e

function show_menu() {
    clear
    echo "=========================================="
    echo "  🚀 CONFIGURACIÓN DE VPS (Ubuntu)"
    echo "=========================================="
    echo "1. Instalar Dependencias del Sistema (Git, Java, Maven, Python)"
    echo "2. Instalar y Configurar PostgreSQL"
    echo "3. Configurar Entorno Virtual (.env y pip)"
    echo "4. Configurar Nginx y Servicios (Frontend/Backend)"
    echo "5. Ejecutar Todo (Opción 1, 2, 3 y 4)"
    echo "0. Salir"
    echo "=========================================="
}

function install_system_deps() {
    echo "[*] Actualizando sistema..."
    sudo apt-get update && sudo apt-get upgrade -y
    echo "[*] Instalando dependencias base..."
    sudo apt-get install -y curl wget git python3 python3-pip python3-venv openjdk-17-jdk maven net-tools nodejs npm
    echo "[+] Dependencias del sistema instaladas."
}

function setup_postgresql() {
    echo "[*] Instalando PostgreSQL..."
    sudo apt-get install -y postgresql postgresql-contrib
    
    echo "=========================================="
    echo "  Configuración de Base de Datos"
    echo "=========================================="
    read -p "Ingresa el nombre del usuario de la DB [diagramador_user]: " DB_USER
    DB_USER=${DB_USER:-diagramador_user}
    
    read -p "Ingresa la contraseña para $DB_USER [12345]: " DB_PASS
    DB_PASS=${DB_PASS:-12345}
    
    read -p "Ingresa el nombre de la base de datos [diagramador_db]: " DB_NAME
    DB_NAME=${DB_NAME:-diagramador_db}
    
    echo "[*] Creando usuario y base de datos..."
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
    
    echo "[+] Base de datos PostgreSQL configurada con éxito."
    
    # Save to a temp file to be used in step 3
    echo "MAIN_DB_URL=postgresql+asyncpg://$DB_USER:$DB_PASS@localhost/$DB_NAME" > /tmp/db_env
}

function setup_env() {
    echo "[*] Creando entorno virtual de Python..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    echo "[*] Instalando dependencias de Python..."
    source venv/bin/activate
    pip install -r requirements.txt
    
    echo "[*] Configurando archivo .env..."
    
    # Auto-detect public IP
    DETECTED_IP=$(curl -s ifconfig.me || echo "127.0.0.1")
    DEFAULT_DOMAIN="http://$DETECTED_IP"
    
    read -p "Ingresa el dominio base o IP (ej. http://midominio.com) [Automático: $DEFAULT_DOMAIN]: " BASE_DOMAIN
    BASE_DOMAIN=${BASE_DOMAIN:-$DEFAULT_DOMAIN}
    
    if [ -f "/tmp/db_env" ]; then
        MAIN_DB_URL=$(cat /tmp/db_env | cut -d'=' -f2-)
    else
        read -p "Ingresa la URL de la base de datos principal [postgresql+asyncpg://user:pass@localhost/db]: " MAIN_DB_URL
    fi
    
    read -p "Ingresa tu API Key de Gemini: " GEMINI_API
    
    cat <<EOF > .env
API_V1_STR=/api/v1
PROJECT_NAME="Deployer Backend"
MAIN_DB_URL=$MAIN_DB_URL
BASE_DOMAIN=$BASE_DOMAIN
GEMINI_API=$GEMINI_API
OPENROUTE_API=$GEMINI_API
EOF
    
    echo "[+] Entorno virtual y .env configurados."
}

function setup_nginx_and_services() {
    echo "[*] Instalando y configurando Nginx..."
    sudo apt-get install -y nginx

    # Frontend Build
    echo "[*] Compilando Frontend (React Build)..."
    cd ../frontend
    npm install
    npm run build
    FRONTEND_DIST_PATH="$(pwd)/dist"
    cd ../deployer_backend

    # Frontend Nginx Config (Static serving)
    if [ ! -f "/etc/nginx/sites-available/diagramador" ]; then
        echo "[*] Creando configuración Nginx para el Frontend estático..."
        sudo bash -c "cat <<EOF > /etc/nginx/sites-available/diagramador
server {
    listen 80;
    server_name diagramador.gerlextech.com;

    root $FRONTEND_DIST_PATH;
    index index.html;

    location / {
        try_files \\\$uri \\\$uri/ /index.html;
    }
}
EOF"
    else
        echo "[!] Configuración de Nginx para frontend ya existe. Omitiendo."
    fi

    # Backend Nginx Config
    if [ ! -f "/etc/nginx/sites-available/api-diagramador" ]; then
        echo "[*] Creando configuración Nginx para el Backend..."
        sudo bash -c 'cat <<EOF > /etc/nginx/sites-available/api-diagramador
server {
    listen 80;
    server_name api.diagramador.gerlextech.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF'
    else
        echo "[!] Configuración de Nginx para backend ya existe. Omitiendo."
    fi

    echo "[*] Habilitando sitios y reiniciando Nginx..."
    sudo ln -sf /etc/nginx/sites-available/diagramador /etc/nginx/sites-enabled/
    sudo ln -sf /etc/nginx/sites-available/api-diagramador /etc/nginx/sites-enabled/
    
    if sudo nginx -t; then
        sudo systemctl reload nginx
        echo "[+] Nginx recargado con éxito."
    else
        echo "[-] Error de sintaxis en Nginx, no se recargó."
    fi

    echo "[*] Configurando servicios SystemD..."

    # Backend Service
    if [ ! -f "/etc/systemd/system/diagramador-backend.service" ]; then
        echo "[*] Creando servicio SystemD para Backend..."
        sudo bash -c "cat <<EOF > /etc/systemd/system/diagramador-backend.service
[Unit]
Description=Diagramador Backend (FastAPI)
After=network.target

[Service]
User=\$USER
WorkingDirectory=$(pwd)/../backend
Environment=\"PATH=$(pwd)/../backend/venv/bin\"
ExecStart=$(pwd)/../backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
EOF"
        sudo systemctl daemon-reload
        sudo systemctl enable diagramador-backend.service
        sudo systemctl start diagramador-backend.service
    else
        echo "[!] Servicio SystemD Backend ya existe. Omitiendo."
    fi

    echo "[+] Nginx y Servicios configurados con éxito."
}


while true; do
    show_menu
    read -p "Selecciona una opción: " OPTION
    
    case $OPTION in
        1)
            install_system_deps
            read -p "Presiona Enter para continuar..."
            ;;
        2)
            setup_postgresql
            read -p "Presiona Enter para continuar..."
            ;;
        3)
            setup_env
            read -p "Presiona Enter para continuar..."
            ;;
        4)
            setup_nginx_and_services
            read -p "Presiona Enter para continuar..."
            ;;
        5)
            install_system_deps
            setup_postgresql
            setup_env
            setup_nginx_and_services
            echo "[+] INSTALACIÓN COMPLETA."
            echo "Puedes arrancar el manager con: source venv/bin/activate && python manager.py"
            read -p "Presiona Enter para continuar..."
            ;;
        0)
            echo "Saliendo..."
            exit 0
            ;;
        *)
            echo "Opción inválida."
            sleep 1
            ;;
    esac
done
