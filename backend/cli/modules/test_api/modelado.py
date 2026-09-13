import httpx
from rich.table import Table
from backend.cli.console import console

def ejecutar():
    url = "http://localhost:8000/api/v1/modelado/"
    console.print(f"[cyan]Testeando API Modelado ({url})...[/cyan]")
    
    table = Table(title="Test API: Modelado", show_header=True, header_style="bold magenta")
    table.add_column("Endpoint")
    table.add_column("Método")
    table.add_column("Status Code")
    table.add_column("Resultado")

    try:
        response = httpx.get(url, timeout=3.0)
        status = response.status_code
        # Asumiendo 404 porque no existe un endpoint base GET /modelado/ sin auth o sin id
        color = "green" if status in [401, 404] else "red"
        resultado = f"OK ({status} Esperado)" if status in [401, 404] else f"FALLO (dio {status})"
        
        table.add_row("/modelado/", "GET", f"[{color}]{status}[/{color}]", f"[{color}]{resultado}[/{color}]")
    except Exception as e:
        table.add_row("/modelado/", "GET", "[red]ERROR[/red]", f"[red]{str(e)}[/red]")

    console.print(table)
    console.print("\nPresiona Enter para continuar...")
    input()
