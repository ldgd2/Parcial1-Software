import httpx
from rich.table import Table
from backend.cli.console import console

def ejecutar():
    url = "http://localhost:8000/api/v1/proyectos/"
    console.print(f"[cyan]Testeando API Proyectos ({url})...[/cyan]")
    
    table = Table(title="Test API: Proyectos", show_header=True, header_style="bold magenta")
    table.add_column("Endpoint")
    table.add_column("Método")
    table.add_column("Status Code")
    table.add_column("Resultado")

    try:
        response = httpx.get(url, timeout=3.0)
        status = response.status_code
        color = "green" if status == 401 else "red"
        resultado = "OK (401 Esperado)" if status == 401 else f"FALLO (Esperado 401, dio {status})"
        
        table.add_row("/proyectos/", "GET", f"[{color}]{status}[/{color}]", f"[{color}]{resultado}[/{color}]")
    except Exception as e:
        table.add_row("/proyectos/", "GET", "[red]ERROR[/red]", f"[red]{str(e)}[/red]")

    console.print(table)
    console.print("\nPresiona Enter para continuar...")
    input()
