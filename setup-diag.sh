#!/bin/bash

# Script de instalación automática del entorno de desarrollo (Backend y Frontend)
# Ahora con PostgreSQL y fix de permisos (SUDO_USER)

echo "==================================================="
echo " 🚀 AUTOMATED SETUP PARA DIAGRAMADOR"
echo "==================================================="

# Obtener el usuario original si se ejecutó con sudo
REAL_USER=${SUDO_USER:-$USER}

# 1. Instalar dependencias del sistema y PostgreSQL
echo -e "\n[1/4] Instalando dependencias del sistema..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip nodejs npm postgresql postgresql-contrib
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew install python node postgresql
else
    echo "⚠️ Sistema Windows/Otro detectado. Se asume que Python, Node y PostgreSQL ya están listos."
fi

# ==========================================
# SETUP POSTGRESQL
# ==========================================
echo -e "\n[2/4] Configurando PostgreSQL..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    read -p "Ingresa el nombre del usuario de la DB [postgres]: " DB_USER
    DB_USER=${DB_USER:-postgres}
    
    read -p "Ingresa la contraseña para $DB_USER [postgres]: " DB_PASS
    DB_PASS=${DB_PASS:-postgres}
    
    read -p "Ingresa el nombre de la base de datos [diagramador]: " DB_NAME
    DB_NAME=${DB_NAME:-diagramador}

    echo "[*] Creando usuario y base de datos..."
    # Si el rol ya existe, ignoramos el error, pero intentamos crearlo de todos modos
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" || true
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';"
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || true
else
    echo "En Windows/Mac, por favor crea la base de datos manualmente o asegúrate de que esté corriendo."
    DB_USER="postgres"
    DB_PASS="postgres"
    DB_NAME="diagramador"
fi

# ==========================================
# SETUP BACKEND
# ==========================================
echo -e "\n[3/4] Configurando el Backend (FastAPI)..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv || python -m venv venv
fi

echo "Instalando dependencias de Python..."
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

# Configurar variables de entorno con la info de PostgreSQL
if [ ! -f ".env" ]; then
    echo "Generando archivo .env con configuración de PostgreSQL..."
    cat <<EOF > .env
# Database
DB_IP=127.0.0.1
DB_PORT=5432
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASS
DB_NAME=$DB_NAME

# Security
SECRET_KEY=supersecretkey_change_in_production

# GitHub OAuth App (Completar luego)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
ENCRYPTION_MASTER_KEY=
EOF
else
    echo "El archivo .env ya existe. Recuerda configurarlo para apuntar a PostgreSQL."
fi

# ==========================================
# SETUP FRONTEND
# ==========================================
echo -e "\n[4/4] Configurando el Frontend (React/Vite)..."
cd ../frontend
npm install

# ==========================================
# FIX PERMISOS (Para que no dé Permission Denied al usuario normal)
# ==========================================
cd ..
if [ -n "$SUDO_USER" ]; then
    echo "[*] Ajustando permisos de los archivos creados para el usuario $REAL_USER..."
    sudo chown -R $REAL_USER:$REAL_USER backend/venv backend/.env frontend/node_modules 2>/dev/null || true
fi

echo -e "\n==================================================="
echo " 🎉 ¡SETUP COMPLETADO CON ÉXITO! 🎉"
echo "==================================================="
echo "Para solucionar el error de 'Permission denied' en tu .env actual, ejecuta:"
echo "sudo chown ubuntu:ubuntu backend/.env"
echo "==================================================="
