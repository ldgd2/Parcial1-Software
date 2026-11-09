import os
import re
import subprocess
import sys

from rich.prompt import Confirm, Prompt

from backend.cli.console import console, print_header

# backend/cli/modules/db/migrations/menu.py -> backend/
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ALEMBIC_INI = os.path.join(BACKEND_DIR, "alembic.ini")


def _python_del_backend() -> str:
    """Usa el venv del backend si existe; si no, el intérprete que ejecuta el launcher."""
    candidatos = [
        os.path.join(BACKEND_DIR, "venv", "Scripts", "python.exe"),  # Windows
        os.path.join(BACKEND_DIR, "venv", "bin", "python"),          # Linux / macOS
    ]
    for ruta in candidatos:
        if os.path.isfile(ruta):
            return ruta
    return sys.executable


def ejecutar_comando_alembic(comando: list, mostrar: bool = True) -> tuple[bool, str]:
    """
    Ejecuta `alembic -c <backend/alembic.ini> <comando>` desde cualquier carpeta.
    Devuelve (ok, salida). Alembic escribe su log en stderr, por eso se muestran ambos.
    """
    if mostrar:
        console.print(f"\n[dim]Ejecutando: alembic {' '.join(comando)}[/dim]")

    if not os.path.isfile(ALEMBIC_INI):
        console.print(f"[bold red]No se encontró alembic.ini en:[/bold red] {ALEMBIC_INI}")
        return False, ""

    try:
        resultado = subprocess.run(
            [_python_del_backend(), "-m", "alembic", "-c", ALEMBIC_INI] + comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=BACKEND_DIR,
        )
    except Exception as e:
        console.print(f"[bold red]Ocurrió un error inesperado:[/bold red] {e}")
        return False, ""

    salida = "\n".join(s for s in (resultado.stdout.strip(), resultado.stderr.strip()) if s)
    ok = resultado.returncode == 0

    if mostrar:
        if ok:
            console.print("[bold green]Comando ejecutado con éxito.[/bold green]")
        else:
            console.print("[bold red]Error al ejecutar el comando:[/bold red]")
        if salida:
            console.print(salida, markup=False, highlight=False)
    return ok, salida


def _revisiones(texto: str) -> list[str]:
    return re.findall(r"^([0-9a-f]{6,})\b", texto, flags=re.M)


def obtener_estado() -> dict | None:
    """Versión actual de la BD y heads del código. None si no se pudo consultar."""
    ok_h, salida_h = ejecutar_comando_alembic(["heads"], mostrar=False)
    ok_c, salida_c = ejecutar_comando_alembic(["current"], mostrar=False)
    if not (ok_h and ok_c):
        console.print("[bold red]No se pudo consultar el estado de las migraciones:[/bold red]")
        console.print(salida_c or salida_h, markup=False, highlight=False)
        return None
    return {"heads": _revisiones(salida_h), "actual": _revisiones(salida_c)}


def mostrar_estado() -> dict | None:
    estado = obtener_estado()
    if estado is None:
        return None

    heads, actual = estado["heads"], estado["actual"]
    console.print(f"\n[bold]Head(s) en el código:[/bold] {', '.join(heads) or '(ninguno)'}")
    console.print(f"[bold]Versión en la BD:[/bold]      {', '.join(actual) or '(sin versión registrada)'}")

    if len(heads) > 1:
        console.print(
            "\n[bold yellow]⚠ Hay más de un head.[/bold yellow] Dos migraciones salen de la misma revisión; "
            "corrige el `down_revision` de una de ellas para que queden en una sola cadena."
        )
    elif not actual:
        console.print("\n[yellow]La BD no tiene versión registrada. Usa [2] Up para crear el esquema.[/yellow]")
    elif set(actual) == set(heads):
        console.print("\n[bold green]✔ La BD está al día.[/bold green]")
    else:
        console.print("\n[yellow]Hay migraciones pendientes. Usa [2] Up para aplicarlas.[/yellow]")
    return estado


def menu_migrations():
    while True:
        print_header("MANAGER > BASE DE DATOS > MIGRACIONES")
        console.print("[1] Crear nueva migración (Make)")
        console.print("[2] Aplicar migraciones (Up)")
        console.print("[3] Revertir última migración (Down)")
        console.print("[4] Sellar versión en Head (Stamp Head)")
        console.print("[5] Ver estado (versión actual / heads)")
        console.print("[6] Ver historial")
        console.print("[7] Fix estado de migraciones (auto‑repair)")
        console.print("[0] Volver")

        opcion = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3", "4", "5", "6", "7", "0"], default="0")

        if opcion == "1":
            estado = obtener_estado()
            if estado and estado["actual"] and set(estado["actual"]) != set(estado["heads"]):
                console.print("[yellow]La BD no está en head: aplica primero las migraciones pendientes ([2] Up).[/yellow]")
            elif estado and len(estado["heads"]) > 1:
                console.print("[yellow]Hay más de un head: resuélvelo antes de crear otra migración ([5]).[/yellow]")
            else:
                mensaje = Prompt.ask("Ingresa un mensaje para la migración")
                if mensaje:
                    with console.status("[bold cyan]Generando migración..."):
                        ejecutar_comando_alembic(["revision", "--autogenerate", "-m", mensaje])
                    console.print("[dim]Revisa el archivo generado en backend/alembic/versions antes de aplicarlo.[/dim]")
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "2":
            estado = obtener_estado()
            if estado and len(estado["heads"]) > 1:
                console.print("[yellow]Hay más de un head: resuélvelo antes de aplicar ([5] Ver estado).[/yellow]")
            else:
                with console.status("[bold cyan]Aplicando migraciones..."):
                    ejecutar_comando_alembic(["upgrade", "head"])
                mostrar_estado()
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "3":
            estado = mostrar_estado()
            if estado and estado["actual"]:
                if Confirm.ask("\n[bold red]¿Revertir la última migración? Puede borrar tablas o columnas con datos[/bold red]", default=False):
                    with console.status("[bold cyan]Revertiendo migración..."):
                        ejecutar_comando_alembic(["downgrade", "-1"])
            elif estado is not None:
                console.print("[yellow]No hay ninguna migración aplicada que revertir.[/yellow]")
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "4":
            console.print(
                "[dim]Stamp solo marca la BD como actualizada, sin ejecutar nada. "
                "Úsalo cuando las tablas ya existen (por ejemplo, creadas con init_db).[/dim]"
            )
            if Confirm.ask("¿Sellar la BD en head?", default=False):
                with console.status("[bold cyan]Sellando versión en Head..."):
                    ejecutar_comando_alembic(["stamp", "head"])
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "5":
            mostrar_estado()
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "6":
            ejecutar_comando_alembic(["history", "--indicate-current"])
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "7":
    # Auto‑repair migration state using the dedicated fix_state helper
    from .fix_state import fix_state
    console.print("[dim]Ejecutando reparación automática del estado de migraciones...[/dim]")
    fix_state()
    # Mostrar estado actualizado
    estado = obtener_estado()
    if estado:
        mostrar_estado()
    Prompt.ask("\nPresiona Enter para continuar")
            # Auto‑repair migration state
            # 1. Eliminar archivo de revisión obsoleto (hardcoded)
            obsolete = os.path.join(BACKEND_DIR, "alembic", "versions", "e3f4a5b6c7d8_create_plantillas_proyecto.py")
            if os.path.isfile(obsolete):
                try:
                    os.remove(obsolete)
                    console.print(f"[dim]Archivo obsoleto removido: {os.path.basename(obsolete)}[/dim]")
                except Exception as e:
                    console.print(f"[bold red]Error al eliminar el archivo obsoleto:[/bold red] {e}")
            else:
                console.print("[dim]Archivo obsoleto no encontrado; quizás ya fue removido.[/dim]")
            # 2. Corregir referencias a la revisión eliminada en otros archivos
            missing_rev = "e3f4a5b6c7d8"
            # buscar el revision id más reciente que exista
            existing_revs = []
            for fname in os.listdir(os.path.join(BACKEND_DIR, "alembic", "versions")):
                if fname.endswith('.py'):
                    path = os.path.join(BACKEND_DIR, "alembic", "versions", fname)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if f"revision = '{missing_rev}'" in content:
                        continue
                    if f"down_revision = '{missing_rev}'" in content:
                        # replace with the latest existing revision (assume last in sorted list)
                        # collect revision identifiers from all files
                        rev_id = None
                        for line in content.splitlines():
                            if line.strip().startswith('revision ='):
                                rev_id = line.split('=')[1].strip().strip("'\"")
                                break
                        if rev_id:
                            existing_revs.append(rev_id)
            # Determine fallback revision (last existing in alphabetical order)
            fallback_rev = sorted(existing_revs)[-1] if existing_revs else None
            if fallback_rev:
                for fname in os.listdir(os.path.join(BACKEND_DIR, "alembic", "versions")):
                    path = os.path.join(BACKEND_DIR, "alembic", "versions", fname)
                    with open(path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    if f"down_revision = '{missing_rev}'" in text:
                        new_text = text.replace(f"down_revision = '{missing_rev}'", f"down_revision = '{fallback_rev}'")
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_text)
                        console.print(f"[dim]Actualizada down_revision en {fname} a {fallback_rev}[/dim]")
            # 3. Ejecutar stamp head para sincronizar BD
            ok, _ = ejecutar_comando_alembic(["stamp", "head"], mostrar=True)
            if ok:
                console.print("[bold green]Stamp a head ejecutado con éxito.[/bold green]")
            else:
                console.print("[bold red]Falló el stamp a head. Revisa los mensajes anteriores.[/bold red]")
            # 4. Mostrar nuevo estado
            mostrar_estado()
            estado = obtener_estado()
            if not estado:
                Prompt.ask("\nPresiona Enter para continuar")
                continue
            heads = estado["heads"]
            if len(heads) <= 1:
                console.print("[bold green]No hay problemas de heads detectados. Estado ya está limpio.[/bold green]")
                Prompt.ask("\nPresiona Enter para continuar")
                continue
            console.print("[yellow]Detectados múltiples heads. Intentando reparación automática...[/yellow]")
            # Archivo de revisión obsoleto (hardcoded para este proyecto)
            obsolete = os.path.join(BACKEND_DIR, "alembic", "versions", "e3f4a5b6c7d8_create_plantillas_proyecto.py")
            if os.path.isfile(obsolete):
                try:
                    os.remove(obsolete)
                    console.print(f"[dim]Archivo obsoleto removido: {os.path.basename(obsolete)}[/dim]")
                except Exception as e:
                    console.print(f"[bold red]Error al eliminar el archivo obsoleto:[/bold red] {e}")
            else:
                console.print("[dim]Archivo obsoleto no encontrado; quizás ya fue removido.[/dim]")
            # Re‑stamp a head
            ok, _ = ejecutar_comando_alembic(["stamp", "head"], mostrar=True)
            if ok:
                console.print("[bold green]Stamp a head ejecutado con éxito.[/bold green]")
            else:
                console.print("[bold red]Falló el stamp a head. Revisa los mensajes anteriores.[/bold red]")
            # Mostrar nuevo estado
            mostrar_estado()
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "0":
            break

    while True:
        print_header("MANAGER > BASE DE DATOS > MIGRACIONES")
        console.print("[1] Crear nueva migración (Make)")
        console.print("[2] Aplicar migraciones (Up)")
        console.print("[3] Revertir última migración (Down)")
        console.print("[4] Sellar versión en Head (Stamp Head)")
        console.print("[5] Ver estado (versión actual / heads)")
        console.print("[6] Ver historial")
        console.print("[0] Volver")

        opcion = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3", "4", "5", "6", "0"], default="0")

        if opcion == "1":
            estado = obtener_estado()
            if estado and estado["actual"] and set(estado["actual"]) != set(estado["heads"]):
                console.print("[yellow]La BD no está en head: aplica primero las migraciones pendientes ([2] Up).[/yellow]")
            elif estado and len(estado["heads"]) > 1:
                console.print("[yellow]Hay más de un head: resuélvelo antes de crear otra migración ([5]).[/yellow]")
            else:
                mensaje = Prompt.ask("Ingresa un mensaje para la migración")
                if mensaje:
                    with console.status("[bold cyan]Generando migración..."):
                        ejecutar_comando_alembic(["revision", "--autogenerate", "-m", mensaje])
                    console.print("[dim]Revisa el archivo generado en backend/alembic/versions antes de aplicarlo.[/dim]")
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "2":
            estado = obtener_estado()
            if estado and len(estado["heads"]) > 1:
                console.print("[yellow]Hay más de un head: resuélvelo antes de aplicar ([5] Ver estado).[/yellow]")
            else:
                with console.status("[bold cyan]Aplicando migraciones..."):
                    ejecutar_comando_alembic(["upgrade", "head"])
                mostrar_estado()
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "3":
            estado = mostrar_estado()
            if estado and estado["actual"]:
                if Confirm.ask("\n[bold red]¿Revertir la última migración? Puede borrar tablas o columnas con datos[/bold red]", default=False):
                    with console.status("[bold cyan]Revertiendo migración..."):
                        ejecutar_comando_alembic(["downgrade", "-1"])
            elif estado is not None:
                console.print("[yellow]No hay ninguna migración aplicada que revertir.[/yellow]")
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "4":
            console.print(
                "[dim]Stamp solo marca la BD como actualizada, sin ejecutar nada. "
                "Úsalo cuando las tablas ya existen (por ejemplo, creadas con init_db).[/dim]"
            )
            if Confirm.ask("¿Sellar la BD en head?", default=False):
                with console.status("[bold cyan]Sellando versión en Head..."):
                    ejecutar_comando_alembic(["stamp", "head"])
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "5":
            mostrar_estado()
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "6":
            ejecutar_comando_alembic(["history", "--indicate-current"])
            Prompt.ask("\nPresiona Enter para continuar")

        elif opcion == "0":
            break
