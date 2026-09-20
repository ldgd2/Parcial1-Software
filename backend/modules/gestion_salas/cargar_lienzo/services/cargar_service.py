from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_salas.cargar_lienzo.repositories.cargar_repository import cargar_lienzo_repository
from backend.modules.gestion_salas.cargar_lienzo.schemas.response import LienzoResponse


class CargarLienzoService:
    async def cargar_lienzo(
        self, proyecto_id: int, user: Usuario, db: AsyncSession
    ) -> LienzoResponse:
        proyecto = await cargar_lienzo_repository.obtener_proyecto_con_colaboradores(db, proyecto_id)

        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado."
            )

        colaborador = next(
            (c for c in proyecto.colaboradores if c.usuario_id == user.id), None
        )
        if not colaborador or colaborador.estado != "aprobado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado."
            )

        return LienzoResponse(
            proyecto_id=proyecto.id,
            proyecto_nombre=proyecto.nombre,
            codigo_acceso=proyecto.codigo_acceso,
            lienzo_json=proyecto.lienzo_json or "null",
            rol_proyecto=colaborador.rol_proyecto,
            github_repo_url=proyecto.github_repo_url
        )


cargar_lienzo_service = CargarLienzoService()
