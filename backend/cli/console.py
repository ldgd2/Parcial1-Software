from rich.console import Console
from rich.panel import Panel

console = Console()

def print_header(title: str):
    console.clear()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False, border_style="cyan"))
