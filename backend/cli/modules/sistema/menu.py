from backend.cli.console import console, print_header
from rich.prompt import Prompt
from . import crear, editar, eliminar, ver_estado, ver_log_tiempo_real, iniciar, detener, reiniciar

def menu_sistema():
    while True:
        print_header('MÓDULO: SISTEMA')
        console.print('[1] Crear Servicio (Backend/Frontend)')
        console.print('[2] Iniciar Servicio')
        console.print('[3] Detener Servicio')
        console.print('[4] Reiniciar Servicio')
        console.print('[5] Editar Servicio')
        console.print('[6] Eliminar Servicio')
        console.print('[7] Ver Estado')
        console.print('[8] Ver Log (Tiempo Real)')
        console.print('[0] Volver')
        
        op = Prompt.ask('- Selecciona', choices=['1','2','3','4','5','6','7','8','0'], default='0')
        if op == '1': crear.ejecutar()
        elif op == '2': iniciar.ejecutar()
        elif op == '3': detener.ejecutar()
        elif op == '4': reiniciar.ejecutar()
        elif op == '5': editar.ejecutar()
        elif op == '6': eliminar.ejecutar()
        elif op == '7': ver_estado.ejecutar()
        elif op == '8': ver_log_tiempo_real.ejecutar()
        elif op == '0': break
