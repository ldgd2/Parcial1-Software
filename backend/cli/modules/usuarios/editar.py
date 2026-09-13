import asyncio
from backend.cli.console import console
from rich.prompt import Prompt
from .db_executor import get_usuario_db, update_usuario_db

async def async_ejecutar():
    console.print('[cyan]Editar Usuario[/cyan]')
    email = Prompt.ask("Email del usuario a editar")
    
    try:
        user = await get_usuario_db(email)
        if not user:
            console.print(f"[red]No se encontró ningún usuario con el email {email}[/red]")
            input("\nPresiona Enter para continuar...")
            return
            
        console.print(f"[yellow]Usuario actual: {user.nombre}[/yellow]")
        nuevo_nombre = Prompt.ask("Nuevo nombre", default=user.nombre)
        
        exito = await update_usuario_db(email, nuevo_nombre)
        if exito:
            console.print(f'[bold green]✔ Usuario {email} actualizado correctamente.[/bold green]')
        else:
            console.print("[red]Error al actualizar usuario.[/red]")
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        
    input("\nPresiona Enter para continuar...")

def ejecutar():
    asyncio.run(async_ejecutar())
