from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.gestion_usuarios.models import Usuario
from backend.core.permissions.proyecto import es_lector, MENSAJE_SOLO_LECTURA
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
        if es_lector(colaborador):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MENSAJE_SOLO_LECTURA)

        await guardar_lienzo_repository.guardar_lienzo_proyecto(db, proyecto, payload.lienzo)

        # Lo guardado pasa a ser el estado vivo de la sala (base de la sincronización offline)
        from backend.modules.gestion_concurrencia.sincronizacion_tiempo_real.controllers.ws_sync_controller import reiniciar_estado_vivo
        import json as _json
        lienzo = payload.lienzo
        if isinstance(lienzo, str):
            try:
                lienzo = _json.loads(lienzo)
            except ValueError:
                lienzo = None
        reiniciar_estado_vivo(proyecto.codigo_acceso, lienzo if isinstance(lienzo, dict) else None)

        return GuardarLienzoResponse(detail="Lienzo guardado exitosamente.")


guardar_lienzo_service = GuardarLienzoService()
