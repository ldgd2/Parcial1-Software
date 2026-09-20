from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.gestion_usuarios.models import Usuario
from backend.core.websockets.connection_manager import manager
from backend.modules.gestion_salas.unirse_sala.repositories.unirse_repository import unirse_sala_repository
from backend.modules.gestion_salas.unirse_sala.schemas.response import UnirseSalaResponse


class UnirseSalaService:
    async def unirse_a_sala(
        self, codigo_acceso: str, user: Usuario, db: AsyncSession
    ) -> UnirseSalaResponse:
        proyecto = await unirse_sala_repository.obtener_proyecto_por_codigo(db, codigo_acceso)

        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Código de acceso inválido o proyecto no encontrado."
            )

        colaborador = next(
            (c for c in proyecto.colaboradores if c.usuario_id == user.id), None
        )

        if not colaborador:
            await unirse_sala_repository.crear_solicitud_colaborador(db, proyecto.id, user.id)

            await manager.notify_host(proyecto.codigo_acceso, {
                "type": "join_request",
                "guest_id": f"auth_{user.id}",
                "nickname": user.nombre
            })

            return UnirseSalaResponse(
                acceso="pendiente",
                mensaje="Solicitud enviada al anfitrión. Espera su aprobación.",
                proyecto_id=proyecto.id,
                proyecto_nombre=proyecto.nombre
            )

        if colaborador.estado == "rechazado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu solicitud fue rechazada. Contacta al anfitrión del proyecto."
            )

        if colaborador.estado == "pendiente":
            await manager.notify_host(proyecto.codigo_acceso, {
                "type": "join_request",
                "guest_id": f"auth_{user.id}",
                "nickname": user.nombre
            })
            return UnirseSalaResponse(
                acceso="pendiente",
                mensaje="Tu solicitud sigue pendiente de aprobación.",
                proyecto_id=proyecto.id,
                proyecto_nombre=proyecto.nombre
            )

        return UnirseSalaResponse(
            acceso="aprobado",
            proyecto_id=proyecto.id,
            proyecto_nombre=proyecto.nombre,
            codigo_acceso=proyecto.codigo_acceso,
            lienzo_json=proyecto.lienzo_json,
            github_repo_url=proyecto.github_repo_url
        )


unirse_sala_service = UnirseSalaService()
