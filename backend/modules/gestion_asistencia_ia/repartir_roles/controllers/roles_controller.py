"""
Compatibilidad retroactiva: Re-exportación desde el paquete canónico gestión_proyectos_asistida.
"""
from backend.modules.gestion_proyectos_asistida.repartir_roles.controllers.roles_controller import (
    router,
    repartir_roles,
    obtener_roles_proyecto,
    asignar_rol_manual,
)

__all__ = ["router", "repartir_roles", "obtener_roles_proyecto", "asignar_rol_manual"]
