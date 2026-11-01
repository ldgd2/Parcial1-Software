#!/bin/bash

# Si se ejecuta con sh/dash, relanzar con bash si está disponible
if [ -z "$BASH_VERSION" ] && [ -x /bin/bash ]; then
    exec /bin/bash "$0" "$@"
fi

# Script de instalacion automatica del entorno de desarrollo (Backend y Frontend)
# PostgreSQL y ajuste de permisos (SUDO_USER)

printf "%s\n" "==================================================="
printf "%s\n" " AUTOMATED SETUP PARA DIAGRAMADOR"
printf "%s\n" "==================================================="

# Obtener el usuario original si se ejecuto con sudo
REAL_USER=${SUDO_USER:-$USER}
OS_NAME=$(uname -s 2>/dev/null || echo "Unknown")

# 1. Instalar dependencias del sistema y PostgreSQL
printf "\n[1/4] Instalando dependencias del sistema...\n"
case "$OS_NAME" in
    Linux*)
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv python3-pip nodejs npm postgresql postgresql-contrib nginx
        sudo systemctl start postgresql 2>/dev/null || sudo service postgresql start 2>/dev/null || true
        ;;
    Darwin*)
        brew install python node postgresql
        brew services start postgresql 2>/dev/null || true
        ;;
    *)
        printf "%s\n" "Sistema Windows/Otro detectado. Se asume que Python, Node y PostgreSQL ya estan listos."
        ;;
esac

# ==========================================
# SETUP POSTGRESQL
# ==========================================
printf "\n[2/4] Configurando PostgreSQL...\n"
case "$OS_NAME" in
    Linux*)
        printf "%s" "Ingresa el nombre del usuario de la DB [postgres]: "
        read -r DB_USER
        DB_USER=${DB_USER:-postgres}

        printf "%s" "Ingresa la contraseña para $DB_USER [postgres]: "
        read -r DB_PASS
        DB_PASS=${DB_PASS:-postgres}

        printf "%s" "Ingresa el nombre de la base de datos [diagramador]: "
        read -r DB_NAME
        DB_NAME=${DB_NAME:-diagramador}

        printf "%s\n" "[*] Creando usuario y base de datos..."
        sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || true
        sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';"
        sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || true
        ;;
    *)
        printf "%s\n" "En Windows/Mac, por favor crea la base de datos manualmente o asegurate de que este corriendo."
        DB_USER="postgres"
        DB_PASS="postgres"
        DB_NAME="diagramador"
        ;;
esac

# ==========================================
# SETUP BACKEND
# ==========================================
printf "\n[3/4] Configurando el Backend (FastAPI)...\n"
cd backend || exit 1

if [ ! -f "venv/bin/activate" ] && [ ! -f "venv/Scripts/activate" ]; then
    printf "%s\n" "Creando entorno virtual..."
    rm -rf venv 2>/dev/null || true
    python3 -m venv venv || python -m venv venv
fi

printf "%s\n" "Instalando dependencias de Python..."
if [ -f "venv/Scripts/activate" ]; then
    . venv/Scripts/activate
else
    . venv/bin/activate
fi

python3 -m pip install --upgrade pip || pip install --upgrade pip
pip install -r requirements.txt

# Configurar variables de entorno con la info de PostgreSQL
if [ ! -f ".env" ]; then
    printf "%s\n" "Generando archivo .env con configuracion de PostgreSQL..."
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
    printf "%s\n" "El archivo .env ya existe. Recuerda configurarlo para apuntar a PostgreSQL."
fi

# ==========================================
# SETUP FRONTEND
# ==========================================
printf "\n[4/4] Configurando el Frontend (React/Vite)...\n"
cd ../frontend || exit 1
npm install

# ==========================================
# FIX PERMISOS
# ==========================================
cd ..
if [ -n "$SUDO_USER" ]; then
    printf "%s\n" "[*] Ajustando permisos de los archivos creados para el usuario $REAL_USER..."
    sudo chown -R "$REAL_USER:$REAL_USER" backend/venv backend/.env frontend/node_modules frontend/package-lock.json 2>/dev/null || true
fi

printf "\n%s\n" "==================================================="
printf "%s\n" " SETUP COMPLETADO CON EXITO"
printf "%s\n" "==================================================="
