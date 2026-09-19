import os
import sys
import asyncio
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    clear_screen()
    print("="*50)
    print("  🚀 DEPLOYER BACKEND - MANAGER INTERACTIVO")
    print("="*50)
    print("1. Iniciar Servidor Deployer (Uvicorn)")
    print("2. Inicializar Alembic (Crear carpeta migrations)")
    print("3. Crear nueva migración (makemigrations)")
    print("4. Aplicar migraciones (migrate)")
    print("5. Limpiar workspace (Eliminar proyectos)")
    print("6. Ver puertos en uso (Linux)")
    print("0. Salir")
    print("="*50)

def init_alembic():
    if not os.path.exists("alembic"):
        print("Inicializando Alembic...")
        subprocess.run(["alembic", "init", "-t", "async", "alembic"])
        print("\n[!] Importante: Se ha creado la carpeta alembic.")
        print("Asegúrate de editar alembic/env.py para importar tus modelos.")
    else:
        print("Alembic ya está inicializado.")

def make_migrations():
    msg = input("Ingresa un mensaje para la migración: ")
    if msg.strip():
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", msg])
    else:
        print("El mensaje no puede estar vacío.")

def migrate():
    print("Aplicando migraciones a SQLite...")
    subprocess.run(["alembic", "upgrade", "head"])

def run_server():
    print("Iniciando servidor en el puerto 8001...")
    subprocess.run([sys.executable, "main.py"])

def clean_workspace():
    workspace = "workspace"
    if not os.path.exists(workspace):
        print("El workspace está limpio.")
        return
    confirm = input(f"¿Estás seguro de eliminar el contenido de {workspace}? (s/n): ")
    if confirm.lower() == 's':
        import shutil
        for item in os.listdir(workspace):
            item_path = os.path.join(workspace, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"Error eliminando {item_path}: {e}")
        print("Workspace limpiado.")

def show_ports():
    print("Puertos en uso en el servidor:")
    if os.name == 'nt':
        subprocess.run(["netstat", "-ano", "|", "findstr", "LISTENING"], shell=True)
    else:
        subprocess.run(["ss", "-tulpn"], shell=True)

def main():
    while True:
        print_menu()
        opcion = input("Elige una opción: ")

        if opcion == "1":
            run_server()
        elif opcion == "2":
            init_alembic()
        elif opcion == "3":
            make_migrations()
        elif opcion == "4":
            migrate()
        elif opcion == "5":
            clean_workspace()
        elif opcion == "6":
            show_ports()
        elif opcion == "0":
            print("Saliendo...")
            break
        else:
            print("Opción inválida.")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    # Ensure working directory is deployer_backend
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
