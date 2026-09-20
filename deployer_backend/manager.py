import sys
import os
import subprocess
import shutil

# Asegurar que el entorno de Python reconozca 'deployer_backend' como módulo base
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from cli.console import console, print_header
from rich.prompt import Prompt

def run_server():
    console.print("\n[cyan]Iniciando servidor Deployer (Uvicorn) en el puerto 8001...[/cyan]")
    subprocess.run([sys.executable, "main.py"])

def clean_workspace():
    workspace = "workspace"
    if not os.path.exists(workspace):
        console.print("[yellow]El workspace ya está limpio.[/yellow]")
        return
    confirm = Prompt.ask(f"¿Estás seguro de eliminar el contenido de {workspace}?", choices=["s", "n"], default="n")
    if confirm == 's':
        for item in os.listdir(workspace):
            item_path = os.path.join(workspace, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                console.print(f"[red]Error eliminando {item_path}: {e}[/red]")
        console.print("[bold green]✔ Workspace limpiado correctamente.[/bold green]")

def init_alembic():
    if not os.path.exists("alembic"):
        console.print("[cyan]Inicializando Alembic para SQLite interno...[/cyan]")
        subprocess.run([sys.executable, "-m", "alembic", "init", "-t", "async", "alembic"])
    else:
        console.print("[yellow]Alembic ya está inicializado.[/yellow]")
    
    op = Prompt.ask("¿Crear y aplicar migración inicial?", choices=["s", "n"], default="s")
    if op == 's':
        msg = Prompt.ask("Mensaje de migración", default="init")
        subprocess.run([sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", msg])
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"])

def main_menu():
    while True:
        print_header("MANAGER DEL DEPLOYER BACKEND")
        console.print("[1] Iniciar Servidor Deployer (Modo Dev)")
        console.print("[2] Sistema (Nginx, Systemd)")
        console.print("[3] Base de Datos PostgreSQL (Para Spring Boot)")
        console.print("[4] Configuración (Variables .env)")
        console.print("[5] Base de Datos Interna (SQLite Migraciones)")
        console.print("[6] Limpiar Workspace (Borrar Proyectos Clonados)")
        console.print("[0] Salir")
        
        opcion = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3", "4", "5", "6", "0"], default="0")
        
        if opcion == "1":
            run_server()
        elif opcion == "2":
            from cli.modules.sistema.menu import menu_sistema
            menu_sistema()
        elif opcion == "3":
            from cli.modules.db.postgres_setup import menu_postgres
            menu_postgres()
        elif opcion == "4":
            from cli.modules.config.menu import menu_config
            menu_config()
        elif opcion == "5":
            init_alembic()
            input("Presiona Enter para continuar...")
        elif opcion == "6":
            clean_workspace()
            input("Presiona Enter para continuar...")
        elif opcion == "0":
            console.print("\n[bold green]Saliendo del Manager del Deployer... ¡Hasta luego![/bold green]")
            break

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main_menu()
