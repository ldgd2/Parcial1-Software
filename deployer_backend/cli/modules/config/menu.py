import os
from cli.console import console, print_header
from rich.prompt import Prompt
from dotenv import set_key, load_dotenv

ENV_FILE = os.path.join(os.path.dirname(__file__), "../../../.env")

def menu_config():
    while True:
        print_header("Configuración (.env) del Deployer")
        
        load_dotenv(ENV_FILE)
        
        # Current values
        main_api = os.getenv("MAIN_API_URL", "https://api-diagramador.gerlextech.com")
        server_host = os.getenv("SERVER_HOST", "localhost")
        pg_password = os.getenv("PG_PASSWORD", "postgres")
        
        console.print(f"[bold yellow]1.[/bold yellow] MAIN_API_URL: [green]{main_api}[/green]")
        console.print(f"[bold yellow]2.[/bold yellow] SERVER_HOST: [green]{server_host}[/green]")
        console.print(f"[bold yellow]3.[/bold yellow] PG_PASSWORD: [green]{pg_password}[/green]")
        console.print("[0] Volver")
        
        op = Prompt.ask("\n¿Qué variable deseas actualizar? (Dejar en blanco para mantener actual)", default="0")
        
        if op == "0":
            break
            
        key_map = {
            "1": "MAIN_API_URL",
            "2": "SERVER_HOST",
            "3": "PG_PASSWORD"
        }
        
        if op in key_map:
            key = key_map[op]
            current_val = os.getenv(key, "")
            new_val = Prompt.ask(f"Nuevo valor para {key} (Actual: {current_val})")
            if new_val.strip() != "":
                if not os.path.exists(ENV_FILE):
                    open(ENV_FILE, 'w').close()
                set_key(ENV_FILE, key, new_val)
                console.print(f"[bold green]✔ {key} actualizado correctamente a '{new_val}'[/bold green]")
                input("Presiona Enter para continuar...")
        else:
            console.print("[red]Opción inválida[/red]")
