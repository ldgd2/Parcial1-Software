"""CU38: ver y cambiar el permiso (editor/lector) de los miembros de un proyecto."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.permissions.proyecto import nivel_en_proyecto, requiere_proyecto
from backend.modules.gestion_proyectos.permisos_proyecto import permisos_service

router = APIRouter(prefix="/api/proyectos", tags=["Proyectos - Permisos (CU38)"])


class CambiarPermisoRequest(BaseModel):
    permiso: str = Field(..., pattern="^(edit|view)$", description="edit = editor, view = lector")


@router.get("/{proyecto_id}/miembros")
async def miembros(proyecto_id: int, db: AsyncSession = Depends(get_db), _=Depends(requiere_proyecto("lector"))) -> List[Dict[str, Any]]:
    return await permisos_service.listar_miembros(db, proyecto_id)


@router.get("/{proyecto_id}/mi-permiso")
async def mi_permiso(proyecto_id: int, db: AsyncSession = Depends(get_db), usuario=Depends(requiere_proyecto("lector"))) -> Dict[str, Any]:
    return {"nivel": await nivel_en_proyecto(db, proyecto_id, usuario.id)}


@router.put("/{proyecto_id}/miembros/{usuario_id}/permiso")
async def cambiar_permiso(
    proyecto_id: int, usuario_id: int, req: CambiarPermisoRequest,
    db: AsyncSession = Depends(get_db), _=Depends(requiere_proyecto("anfitrion")),
) -> Dict[str, Any]:
    return await permisos_service.cambiar_permiso(db, proyecto_id, usuario_id, req.permiso)
