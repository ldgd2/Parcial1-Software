import asyncio
from backend.cli.console import console
from rich.prompt import Prompt
from .db_executor import create_usuario_db

async def async_ejecutar():
    console.print('[cyan]Crear Nuevo Usuario[/cyan]')
    nombre = Prompt.ask("Nombre")
    email = Prompt.ask("Email")
    
    try:
        user = await create_usuario_db(nombre, email)
        console.print(f'[bold green]✔ Usuario {user.nombre} creado correctamente con ID: {user.id}[/bold green]')
    except Exception as e:
        console.print(f"[bold red]Error al crear usuario: {str(e)}[/bold red]")
        
    input("\nPresiona Enter para continuar...")

def ejecutar():
    asyncio.run(async_ejecutar())
