from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_proyectos.compartir_proyecto.repositories.compartir_repo import compartir_repo
from backend.modules.gestion_proyectos.administrar_proyecto.services.admin_service import _verificar_anfitrion
from backend.modules.gestion_proyectos.compartir_proyecto.schemas.response import CompartirLinkResponse

async def obtener_link_compartir(proyecto_id: int, request: Request, user: Usuario, db: AsyncSession):
    # Validar que es el anfitrión
    await _verificar_anfitrion(db, proyecto_id, user.id)
    
    proyecto = await compartir_repo.get(db, id=proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
        
    # Construir el link en base a la URL actual del servidor
    base_url = str(request.base_url).rstrip("/")
    # Asumiendo que el front-end ruteará /proyecto/{uuid}
    link = f"{base_url}/proyecto/{proyecto.codigo_acceso}"
    
    return CompartirLinkResponse(codigo_acceso=proyecto.codigo_acceso, link=link)

async def solicitar_unirse(codigo_acceso: str, user: Usuario, db: AsyncSession):
    proyecto = await compartir_repo.get_proyecto_by_codigo(db, codigo_acceso)
    if not proyecto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código de acceso inválido")
        
    colaborador = await compartir_repo.solicitar_unirse(db, proyecto.id, user.id)
    
    if colaborador.estado == "aprobado":
        return {"detail": "Ya eres colaborador de este proyecto."}
    return {"detail": "Solicitud enviada al anfitrión exitosamente. Por favor, espera su aprobación."}
