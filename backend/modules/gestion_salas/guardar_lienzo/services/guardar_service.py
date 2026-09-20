from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_salas.guardar_lienzo.repositories.guardar_repository import guardar_lienzo_repository
from backend.modules.gestion_salas.guardar_lienzo.schemas.request import GuardarLienzoRequest
from backend.modules.gestion_salas.guardar_lienzo.schemas.response import GuardarLienzoResponse


class GuardarLienzoService:
    async def guardar_lienzo(
        self, proyecto_id: int, payload: GuardarLienzoRequest, user: Usuario, db: AsyncSession
    ) -> GuardarLienzoResponse:
        proyecto = await guardar_lienzo_repository.obtener_proyecto_con_colaboradores(db, proyecto_id)

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

        await guardar_lienzo_repository.guardar_lienzo_proyecto(db, proyecto, payload.lienzo)

        return GuardarLienzoResponse(detail="Lienzo guardado exitosamente.")


guardar_lienzo_service = GuardarLienzoService()
