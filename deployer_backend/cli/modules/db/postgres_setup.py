import os
import subprocess
from cli.console import console, print_header
from rich.prompt import Prompt
from dotenv import load_dotenv, set_key

ENV_FILE = os.path.join(os.path.dirname(__file__), "../../../../.env")

def menu_postgres():
    while True:
        print_header("Configuración de PostgreSQL (Requisito Spring Boot)")
        
        console.print("Este submódulo te permite instalar PostgreSQL y configurar la contraseña")
        console.print("del usuario 'postgres' en este VPS, lo cual es obligatorio para los")
        console.print("despliegues automáticos del motor IA.")
        
        console.print("\n[1] Instalar PostgreSQL (apt-get)")
        console.print("[2] Cambiar contraseña del usuario 'postgres' y guardar en .env")
        console.print("[0] Volver")
        
        op = Prompt.ask("\nSelecciona una opción", default="0")
        
        if op == "1":
            if os.name != 'nt':
                console.print("[cyan]Instalando PostgreSQL...[/cyan]")
                subprocess.run(["sudo", "apt-get", "update"])
                subprocess.run(["sudo", "apt-get", "install", "-y", "postgresql", "postgresql-contrib"])
                console.print("[bold green]✔ PostgreSQL instalado.[/bold green]")
            else:
                console.print("[yellow]Instalación automática solo disponible en Linux.[/yellow]")
            input("Presiona Enter para continuar...")
            
        elif op == "2":
            if os.name != 'nt':
                new_pass = Prompt.ask("Ingresa la nueva contraseña para el superusuario postgres (Recomendado: postgres)")
                if new_pass:
                    try:
                        # Set postgres password using sudo -u postgres psql
                        sql = f"ALTER USER postgres WITH PASSWORD '{new_pass}';"
                        subprocess.run(["sudo", "-u", "postgres", "psql", "-c", sql], check=True)
                        
                        # Save to .env
                        if not os.path.exists(ENV_FILE):
                            open(ENV_FILE, 'w').close()
                        set_key(ENV_FILE, "PG_PASSWORD", new_pass)
                        
                        console.print(f"[bold green]✔ Contraseña de postgres actualizada en DB y .env[/bold green]")
                    except Exception as e:
                        console.print(f"[bold red]Error al configurar PostgreSQL: {e}[/bold red]")
            else:
                console.print("[yellow]Mock en Windows: Solo actualizando .env[/yellow]")
                new_pass = Prompt.ask("Ingresa la nueva contraseña para postgres")
                if not os.path.exists(ENV_FILE):
                    open(ENV_FILE, 'w').close()
                set_key(ENV_FILE, "PG_PASSWORD", new_pass)
                console.print(f"[bold green]✔ Guardado en .env localmente.[/bold green]")
            input("Presiona Enter para continuar...")
            
        elif op == "0":
            break
