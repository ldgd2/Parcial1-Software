from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.gestion_proyectos.crear_proyecto.schemas.request import ProyectoCreate
from backend.modules.gestion_proyectos.crear_proyecto.repositories.proyecto_repo import proyecto_repo
from backend.core.permissions.service import permisos
from backend.modules.gestion_usuarios.models import Usuario

async def crear_nuevo_proyecto(data: ProyectoCreate, user: Usuario, db: AsyncSession):
    # Verificamos si el usuario tiene permiso global para crear proyectos
    await permisos.crearProyecto(user)
    
    return await proyecto_repo.crear_con_anfitrion(db, data, user.id)
