from rich.console import Console
from rich.panel import Panel

console = Console()

def print_header(title):
    import os
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", border_style="cyan"))
