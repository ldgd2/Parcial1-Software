from backend.modules.gestion_usuarios.cerrar_sesion.schemas.response import MessageResponse

def procesar_cierre_sesion() -> MessageResponse:
    return MessageResponse(message="Sesión cerrada correctamente. Por favor, elimine el token en el cliente.")
