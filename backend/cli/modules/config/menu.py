from backend.cli.console import console, print_header
from rich.prompt import Prompt
from rich.table import Table

def menu_config():
    while True:
        print_header("MANAGER > CONFIGURACIÓN")
        console.print("[1] Ver Variables de Entorno (.env)")
        console.print("[0] Volver")
        
        opcion = Prompt.ask("\nSelecciona una opción", choices=["1", "0"], default="0")
        
        if opcion == "1":
            from backend.core.config import settings
            tabla = Table(title="Configuraciones Actuales", show_header=True, header_style="bold magenta")
            tabla.add_column("Variable", style="cyan")
            tabla.add_column("Valor", style="green")
            
            # Recorrer configuraciones ocultando contraseñas
            for key, value in settings.model_dump().items():
                val_str = str(value)
                if "PASSWORD" in key or "SECRET" in key:
                    val_str = "********" if value else "[dim]No configurada[/dim]"
                elif not value:
                    val_str = "[dim]No configurada[/dim]"
                tabla.add_row(key, val_str)
                
            console.print(tabla)
            Prompt.ask("\nPresiona Enter para continuar")
            
        elif opcion == "0":
            break
