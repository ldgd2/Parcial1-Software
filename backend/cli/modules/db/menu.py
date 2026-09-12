from backend.cli.console import console, print_header
from rich.prompt import Prompt
from backend.cli.modules.db.migrations.menu import menu_migrations
from backend.cli.modules.db.seeder.menu import menu_seeder

def menu_db():
    while True:
        print_header("MANAGER > BASE DE DATOS")
        console.print("[1] Migraciones")
        console.print("[2] Seeders")
        console.print("[3] Test de Conexión (Ping)")
        console.print("[0] Volver")
        
        opcion = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3", "0"], default="0")
        
        if opcion == "1":
            menu_migrations()
        elif opcion == "2":
            menu_seeder()
        elif opcion == "3":
            with console.status("[bold cyan]Haciendo ping a PostgreSQL..."):
                from backend.core.database import engine
                import asyncio
                async def ping():
                    try:
                        async with engine.connect() as conn:
                            console.print("\n[bold green]¡Conexión exitosa a la base de datos![/bold green]")
                    except Exception as e:
                        console.print(f"\n[bold red]Error al conectar:[/bold red] {e}")
                asyncio.run(ping())
            Prompt.ask("\nPresiona Enter para continuar")
        elif opcion == "0":
            break
