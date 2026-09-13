from backend.cli.console import console, print_header
from rich.prompt import Prompt
from . import crear, editar, eliminar, ver_estado

def menu_usuarios():
    while True:
        print_header('MÓDULO: USUARIOS')
        console.print('[1] Crear Usuario')
        console.print('[2] Editar Usuario')
        console.print('[3] Eliminar Usuario')
        console.print('[4] Ver Estado')
        console.print('[0] Volver')
        op = Prompt.ask('- Selecciona', choices=['1','2','3','4','0'], default='0')
        if op == '1': crear.ejecutar()
        elif op == '2': editar.ejecutar()
        elif op == '3': eliminar.ejecutar()
        elif op == '4': ver_estado.ejecutar()
        elif op == '0': break
