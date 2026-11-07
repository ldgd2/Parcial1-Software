from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user_optional
from ..schemas.request import RegistrarInteraccionRequest, GuardarSnapshotRequest, LimpiarMemoriaRequest
from ..schemas.response import ContextoIAResponse, CompilarContextoResponse
from ..services.contexto_service import ContextoService

router = APIRouter(prefix="/api/ia/contexto", tags=["IA - Contexto Persistente"])


@router.get("/{proyecto_id}", response_model=ContextoIAResponse)
async def obtener_contexto_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> ContextoIAResponse:
    service = ContextoService(db)
    return await service.obtener_contexto(proyecto_id)


@router.post("/interaccion", response_model=ContextoIAResponse)
async def registrar_interaccion_ia(
    req: RegistrarInteraccionRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> ContextoIAResponse:
    service = ContextoService(db)
    return await service.registrar_interaccion(req)


@router.post("/snapshot", response_model=ContextoIAResponse)
async def guardar_snapshot_diagrama(
    req: GuardarSnapshotRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> ContextoIAResponse:
    service = ContextoService(db)
    return await service.guardar_snapshot(req)


@router.get("/{proyecto_id}/compilado", response_model=CompilarContextoResponse)
async def compilar_contexto_llm(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> CompilarContextoResponse:
    service = ContextoService(db)
    return await service.compilar_contexto(proyecto_id)


@router.post("/limpiar", response_model=ContextoIAResponse)
async def limpiar_memoria_contexto(
    req: LimpiarMemoriaRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> ContextoIAResponse:
    service = ContextoService(db)
    return await service.limpiar_memoria(req)

