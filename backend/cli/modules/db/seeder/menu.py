import asyncio
from backend.cli.console import console, print_header
from rich.prompt import Prompt
from backend.cli.modules.db.seeder.seeder import correr_master_seeder

def menu_seeder():
    while True:
        print_header("MANAGER > BASE DE DATOS > SEEDERS")
        console.print("[1] Ejecutar Seeder Padre (Todos los módulos)")
        console.print("[0] Volver")
        
        opcion = Prompt.ask("\nSelecciona una opción", choices=["1", "0"], default="0")
        
        if opcion == "1":
            cantidad = Prompt.ask("¿Cuántos registros dinámicos deseas generar por módulo?", default="10")
            try:
                cantidad = int(cantidad)
                with console.status("[bold cyan]Ejecutando Seeders..."):
                    asyncio.run(correr_master_seeder(cantidad))
                console.print("\n[bold green]Proceso de Seeding completado exitosamente.[/bold green]")
            except ValueError:
                console.print("[bold red]La cantidad debe ser un número entero.[/bold red]")
            
            Prompt.ask("\nPresiona Enter para continuar")
            
        elif opcion == "0":
            break
