from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user_optional
from ..schemas.request import (
    RegistrarInteraccionRequest,
    GuardarSnapshotRequest,
    LimpiarMemoriaRequest,
    ActualizarVersionDespuesRequest,
    CrearVersionRequest,
    DecidirPropuestaRequest,
)
from ..schemas.response import (
    ContextoIAResponse,
    CompilarContextoResponse,
    VersionDetalle,
    VersionResumen,
    VersionesPagina,
)
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


# ─── Versiones del diagrama antes/después de cada interacción de la IA ──────

@router.get("/{proyecto_id}/versiones", response_model=VersionesPagina)
async def listar_versiones(
    proyecto_id: int,
    limite: int = Query(30, ge=1, le=100),
    antes_de_id: Optional[int] = Query(None, description="Paginación: versiones con id menor a este"),
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> VersionesPagina:
    """Historial completo (más reciente primero), sin el contenido del diagrama."""
    service = ContextoService(db)
    return await service.listar_versiones(proyecto_id, limite, antes_de_id)


@router.post("/{proyecto_id}/versiones", response_model=VersionResumen, status_code=201)
async def crear_version(
    proyecto_id: int,
    req: CrearVersionRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> VersionResumen:
    """Versión de un cambio hecho sin la IA (o restauración). No modifica la memoria de la IA."""
    service = ContextoService(db)
    return await service.crear_version(proyecto_id, req)


@router.get("/{proyecto_id}/versiones/{version_id}", response_model=VersionDetalle)
async def obtener_version(
    proyecto_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> VersionDetalle:
    """Una versión con el diagrama antes y después del cambio."""
    service = ContextoService(db)
    return await service.obtener_version(proyecto_id, version_id)


@router.post("/{proyecto_id}/versiones/{version_id}/decision", response_model=VersionDetalle)
async def decidir_propuesta(
    proyecto_id: int,
    version_id: int,
    req: DecidirPropuestaRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(get_current_user_optional),
) -> VersionDetalle:
    """Aprueba o rechaza una propuesta de la IA. Responde 409 si alguien ya la decidió."""
    service = ContextoService(db)
    return await service.decidir_propuesta(proyecto_id, version_id, req, usuario)


@router.put("/{proyecto_id}/versiones/{version_id}/despues", response_model=VersionResumen)
async def guardar_version_despues(
    proyecto_id: int,
    version_id: int,
    req: ActualizarVersionDespuesRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(get_current_user_optional),
) -> VersionResumen:
    """El frontend envía el diagrama tal como quedó después de aplicar el cambio de la IA."""
    service = ContextoService(db)
    return await service.guardar_version_despues(proyecto_id, version_id, req.estado_despues)
