from fastapi import HTTPException, status
from backend.modules.gestion_usuarios.models import Usuario

class GestorPermisos:
    """Clase utilitaria para validar permisos programáticamente dentro de los endpoints."""
    
    def _verificar(self, user: Usuario, nombre_permiso: str):
        if not user.rol:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Acceso denegado: El usuario no tiene un rol asignado."
            )
            
        tiene_permiso = any(p.nombre == nombre_permiso for p in user.rol.permisos)
        if not tiene_permiso:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado. Acción requiere el permiso: '{nombre_permiso}'"
            )

    async def crearProyecto(self, user: Usuario):
        self._verificar(user, "crear_proyecto")

    async def editarProyecto(self, user: Usuario):
        self._verificar(user, "editar_proyecto")

    async def verProyecto(self, user: Usuario):
        self._verificar(user, "ver_proyecto")

# Instancia singleton para importar en los endpoints
permisos = GestorPermisos()
