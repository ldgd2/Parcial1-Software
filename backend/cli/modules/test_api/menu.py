from backend.cli.console import console, print_header
from rich.prompt import Prompt
from . import usuarios, proyectos, salas, modelado

def menu_test_api():
    while True:
        print_header('MÓDULO: TEST API')
        console.print('[1] Test Usuarios')
        console.print('[2] Test Proyectos')
        console.print('[3] Test Salas')
        console.print('[4] Test Modelado')
        console.print('[0] Volver')
        op = Prompt.ask('- Selecciona', choices=['1','2','3','4','0'], default='0')
        if op == '1': usuarios.ejecutar()
        elif op == '2': proyectos.ejecutar()
        elif op == '3': salas.ejecutar()
        elif op == '4': modelado.ejecutar()
        elif op == '0': break
