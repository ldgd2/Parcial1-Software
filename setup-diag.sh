#!/bin/bash

# Script de instalación automática del entorno de desarrollo (Backend y Frontend)

echo "==================================================="
echo " 🚀 AUTOMATED SETUP PARA DIAGRAMADOR "
echo "==================================================="

# Detectar OS para instalar dependencias de sistema si es Linux
echo -e "\n[1/4] Verificando dependencias del sistema (Python, Node, SQLite)..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Sistema Linux detectado. Instalando paquetes base..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip nodejs npm sqlite3
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Sistema macOS detectado. Instalando paquetes base (requiere Homebrew)..."
    brew install python node sqlite
else
    echo "⚠️ Sistema Windows/Otro detectado. Se asume que Python y Node.js ya están instalados globalmente."
fi

# ==========================================
# SETUP BACKEND
# ==========================================
echo -e "\n[2/4] Configurando el Backend (FastAPI)..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creando entorno virtual de Python..."
    python3 -m venv venv || python -m venv venv
else
    echo "El entorno virtual (venv) ya existe."
fi

echo "Instalando dependencias de Python..."
# Activación cruzada (Windows con Git Bash vs Linux/Mac)
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

# Configurar variables de entorno iniciales
if [ ! -f ".env" ]; then
    echo "Creando archivo .env a partir de .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        echo "API_V1_STR=/api/v1" > .env
        echo "PROJECT_NAME=\"Diagramador API\"" >> .env
        echo "MAIN_DB_URL=sqlite+aiosqlite:///./local_database.db" >> .env
    fi
fi

# ==========================================
# SETUP FRONTEND
# ==========================================
echo -e "\n[3/4] Configurando el Frontend (React/Vite)..."
cd ../frontend

echo "Instalando dependencias de Node.js (esto puede tardar unos minutos)..."
npm install

# ==========================================
# BASE DE DATOS (MIGRACIONES)
# ==========================================
echo -e "\n[4/4] Verificando Base de Datos..."
cd ../backend
echo "Ejecutando migraciones de Alembic si aplican (asegúrate de que la DB esté lista)..."
# alembic upgrade head || echo "⚠️ Revisa la conexión de tu base de datos si esto falla."

echo -e "\n==================================================="
echo " 🎉 ¡SETUP COMPLETADO CON ÉXITO! 🎉"
echo "==================================================="
echo "Tu entorno de desarrollo está listo."
echo ""
echo "💻 PARA EJECUTAR EL BACKEND:"
echo "   cd backend"
echo "   # En Windows: source venv/Scripts/activate"
echo "   # En Linux: source venv/bin/activate"
echo "   uvicorn main:app --reload"
echo "   (o usar tu manager: python manager.py)"
echo ""
echo "🌐 PARA EJECUTAR EL FRONTEND:"
echo "   cd frontend"
echo "   npm run dev"
echo "==================================================="
