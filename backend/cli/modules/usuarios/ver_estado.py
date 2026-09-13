import asyncio
from backend.cli.console import console
from rich.prompt import Prompt
from rich.table import Table
from .db_executor import get_usuario_db, get_all_usuarios

async def async_ejecutar():
    console.print('[blue]Estado de Usuarios[/blue]')
    op = Prompt.ask("Ver todos [1] o buscar uno específico [2]", choices=["1", "2"], default="1")
    
    try:
        if op == "1":
            users = await get_all_usuarios()
            table = Table(title="Lista de Usuarios", show_header=True, header_style="bold magenta")
            table.add_column("ID")
            table.add_column("Nombre")
            table.add_column("Email")
            table.add_column("Estado")
            table.add_column("Tipo")
            
            for u in users:
                estado_color = "[green]Activo[/green]" if u.is_active else "[red]Inactivo[/red]"
                table.add_row(str(u.id), u.nombre, str(u.email), estado_color, u.tipo)
                
            console.print(table)
        else:
            email = Prompt.ask("Email del usuario")
            u = await get_usuario_db(email)
            if u:
                table = Table(title=f"Usuario: {u.nombre}", show_header=True)
                table.add_column("Propiedad")
                table.add_column("Valor")
                table.add_row("ID", str(u.id))
                table.add_row("Email", str(u.email))
                table.add_row("Estado", "Activo" if u.is_active else "Inactivo")
                table.add_row("Tipo", str(u.tipo))
                console.print(table)
            else:
                console.print(f"[red]No se encontró ningún usuario con el email {email}[/red]")
                
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        
    input("\nPresiona Enter para continuar...")

def ejecutar():
    asyncio.run(async_ejecutar())
