from backend.cli.console import console, print_header
from rich.prompt import Prompt
from rich.table import Table

# URLs que en producción NO pueden quedar en localhost (cada una rompía algo distinto)
URLS_PUBLICAS = [
    ("FRONTEND_URL", "Frontend del diagramador (vuelta del login de GitHub, enlaces de avisos)",
     "https://diagramador.{dominio}"),
    ("HOST_DOMAIN", "Dominio del hoster: las apps desplegadas quedan en <HOST_DOMAIN>/host/<usuario>/<proyecto>/",
     "https://host.{dominio}"),
    ("DEPLOYER_URL", "Deployer al que se envía el despliegue (mismo VPS: http://127.0.0.1:8001)",
     "http://127.0.0.1:8001"),
]


def _ocultar(clave: str) -> bool:
    return any(p in clave for p in ("PASSWORD", "SECRET", "KEY", "TOKEN", "API"))


def _ver_variables():
    from backend.core.config import settings
    tabla = Table(title="Configuraciones Actuales", show_header=True, header_style="bold magenta")
    tabla.add_column("Variable", style="cyan")
    tabla.add_column("Valor", style="green")
    # Recorrer configuraciones ocultando contraseñas y claves de API
    for key, value in settings.model_dump().items():
        val_str = str(value)
        if _ocultar(key) and not key.endswith("_URL"):
            val_str = "********" if value else "[dim]No configurada[/dim]"
        elif not value:
            val_str = "[dim]No configurada[/dim]"
        tabla.add_row(key, val_str)
    console.print(tabla)


def _configurar_urls():
    from backend.core.config import settings
    from backend.cli.modules.sistema.servicios_controller import fijar_env_backend

    dominio = Prompt.ask("Dominio base (ej: example.com; vacío = no sugerir)", default="").strip()
    for clave, descripcion, sugerido in URLS_PUBLICAS:
        actual = getattr(settings, clave, "")
        propuesta = sugerido.format(dominio=dominio) if dominio or "{dominio}" not in sugerido else actual
        console.print(f"\n[bold cyan]{clave}[/bold cyan]  [dim]{descripcion}[/dim]")
        console.print(f"   actual: [yellow]{actual}[/yellow]")
        nuevo = Prompt.ask("   nuevo valor (Enter = dejar el propuesto)", default=propuesta).strip().rstrip("/")
        if nuevo and nuevo != actual:
            fijar_env_backend(clave, nuevo)
    console.print("\n[bold green]✔ Listo. Reinicia el backend para aplicar: sudo systemctl restart backend-app[/bold green]")


def menu_config():
    while True:
        print_header("MANAGER > CONFIGURACIÓN")
        console.print("[1] Ver Variables de Entorno (.env)")
        console.print("[2] Configurar URLs públicas (GitHub, hoster, deployer)")
        console.print("[0] Volver")

        opcion = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "0"], default="0")

        if opcion == "1":
            _ver_variables()
            Prompt.ask("\nPresiona Enter para continuar")
        elif opcion == "2":
            _configurar_urls()
            Prompt.ask("\nPresiona Enter para continuar")
        elif opcion == "0":
            break
