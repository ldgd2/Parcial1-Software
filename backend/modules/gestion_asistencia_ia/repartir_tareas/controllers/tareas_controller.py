"""
Compatibilidad retroactiva: Re-exportación desde el paquete canónico gestión_proyectos_asistida.
"""
from backend.modules.gestion_proyectos_asistida.repartir_tareas.controllers.tareas_controller import (
    router,
    repartir_tareas,
    obtener_mis_tareas,
    obtener_todas_las_tareas,
    marcar_tarea,
    crear_tarea_manual,
    eliminar_tarea,
)

__all__ = [
    "router",
    "repartir_tareas",
    "obtener_mis_tareas",
    "obtener_todas_las_tareas",
    "marcar_tarea",
    "crear_tarea_manual",
    "eliminar_tarea",
]
