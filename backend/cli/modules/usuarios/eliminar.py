import asyncio
from backend.cli.console import console
from rich.prompt import Prompt
from .db_executor import delete_usuario_db

async def async_ejecutar():
    console.print('[red]Eliminar Usuario[/red]')
    email = Prompt.ask("Email del usuario a eliminar")
    
    confirm = Prompt.ask(f"¿Estás seguro de eliminar a {email} de la base de datos?", choices=["s", "n"], default="n")
    if confirm == 's':
        try:
            exito = await delete_usuario_db(email)
            if exito:
                console.print(f'[bold green]✔ Usuario {email} eliminado correctamente.[/bold green]')
            else:
                console.print(f"[red]No se encontró el usuario {email}[/red]")
        except Exception as e:
            console.print(f"[bold red]Error: {str(e)}[/bold red]")
    else:
        console.print("[yellow]Operación cancelada.[/yellow]")
        
    input("\nPresiona Enter para continuar...")

def ejecutar():
    asyncio.run(async_ejecutar())
