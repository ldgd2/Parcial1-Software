import sys
import os

# Asegurar que el entorno de Python reconozca 'backend' como módulo base
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.cli.console import console, print_header
from backend.cli.modules.db.menu import menu_db
from rich.prompt import Prompt

def main_menu():
    while True:
        print_header("MANAGER PRINCIPAL")
        console.print("[1] Base de Datos (Migraciones, Seeders)")
        console.print("[2] Configuración")
        console.print("[0] Salir")
        
        opcion = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "0"], default="0")
        
        if opcion == "1":
            menu_db()
        elif opcion == "2":
            from backend.cli.modules.config.menu import menu_config
            menu_config()
        elif opcion == "0":
            console.print("\n[bold green]Saliendo del Manager... ¡Hasta luego![/bold green]")
            break

if __name__ == "__main__":
    main_menu()
