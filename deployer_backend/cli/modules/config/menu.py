import os
from cli.console import console, print_header
from rich.prompt import Prompt
from dotenv import set_key, load_dotenv

ENV_FILE = os.path.join(os.path.dirname(__file__), "../../../.env")

def menu_config():
    while True:
        print_header("Configuracion (.env) del Deployer")
        
        load_dotenv(ENV_FILE, override=True)
        
        variables = [
            ("MAIN_API_URL", "URL del backend principal (diagramador)", "http://localhost:8000"),
            ("SERVER_DOMAIN", "Dominio publico para apps desplegadas (ej: https://host.example.com)", "http://localhost"),
            ("SERVER_HOST", "IP o hostname de este VPS", "localhost"),
            ("PG_PASSWORD", "Password de PostgreSQL (admin)", "postgres"),
            ("PG_HOST", "Host de PostgreSQL", "127.0.0.1"),
            ("MAIN_DB_URL", "URL completa de la BD principal", "postgresql+asyncpg://postgres:postgres@localhost/diagramador_db"),
        ]
        
        for i, (key, desc, default) in enumerate(variables, 1):
            val = os.getenv(key, default)
            console.print(f"[bold yellow]{i}.[/bold yellow] {key}: [green]{val}[/green]  [dim]({desc})[/dim]")
        
        console.print("[0] Volver")
        
        op = Prompt.ask("\nSelecciona variable a actualizar", default="0")
        
        if op == "0":
            break
            
        try:
            idx = int(op) - 1
            if 0 <= idx < len(variables):
                key, desc, default = variables[idx]
                current_val = os.getenv(key, default)
                new_val = Prompt.ask(f"Nuevo valor para {key} (Actual: {current_val})")
                if new_val.strip() != "":
                    if not os.path.exists(ENV_FILE):
                        open(ENV_FILE, 'w').close()
                    set_key(ENV_FILE, key, new_val)
                    console.print(f"[bold green]>> {key} actualizado a '{new_val}'[/bold green]")
                    input("Presiona Enter para continuar...")
            else:
                console.print("[red]Opcion invalida[/red]")
        except ValueError:
            console.print("[red]Opcion invalida[/red]")
