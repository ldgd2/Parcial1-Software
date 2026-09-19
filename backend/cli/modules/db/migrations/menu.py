import subprocess
import sys
import os
from backend.cli.console import console, print_header
from rich.prompt import Prompt

def ejecutar_comando_alembic(comando: list):
    console.print(f"\n[dim]Ejecutando: alembic {' '.join(comando)}[/dim]")
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
        resultado = subprocess.run([sys.executable, "-m", "alembic"] + comando, capture_output=True, text=True, cwd=base_dir)
        if resultado.returncode == 0:
            console.print("[bold green]Comando ejecutado con éxito.[/bold green]")
            if resultado.stdout:
                console.print(resultado.stdout)
        else:
            console.print("[bold red]Error al ejecutar el comando:[/bold red]")
            console.print(resultado.stderr)
    except Exception as e:
        console.print(f"[bold red]Ocurrió un error inesperado:[/bold red] {e}")

def menu_migrations():
    while True:
        print_header("MANAGER > BASE DE DATOS > MIGRACIONES")
        console.print("[1] Crear nueva migración (Make)")
        console.print("[2] Aplicar migraciones (Up)")
        console.print("[3] Revertir última migración (Down)")
        console.print("[0] Volver")
        
        opcion = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3", "0"], default="0")
        
        if opcion == "1":
            mensaje = Prompt.ask("Ingresa un mensaje para la migración")
            if mensaje:
                with console.status("[bold cyan]Generando migración..."):
                    ejecutar_comando_alembic(["revision", "--autogenerate", "-m", mensaje])
            Prompt.ask("\nPresiona Enter para continuar")
            
        elif opcion == "2":
            with console.status("[bold cyan]Aplicando migraciones..."):
                ejecutar_comando_alembic(["upgrade", "head"])
            Prompt.ask("\nPresiona Enter para continuar")
            
        elif opcion == "3":
            with console.status("[bold cyan]Revertiendo migración..."):
                ejecutar_comando_alembic(["downgrade", "-1"])
            Prompt.ask("\nPresiona Enter para continuar")
            
        elif opcion == "0":
            break
