from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.permissions.proyecto import requiere_proyecto, usuario_requerido, verificar_permiso
from ..schemas.request import (
    RegistrarInteraccionRequest,
    GuardarSnapshotRequest,
    LimpiarMemoriaRequest,
    ActualizarVersionDespuesRequest,
    CrearVersionRequest,
    DecidirPropuestaRequest,
    CrearMemoriaRequest,
    EditarMemoriaRequest,
    ResolverConflictoRequest,
)
from ..schemas.response import (
    ContextoIAResponse,
    CompilarContextoResponse,
    VersionDetalle,
    VersionResumen,
    VersionesPagina,
    MemoriaItem,
)
from typing import List
from ..services.contexto_service import ContextoService

router = APIRouter(prefix="/api/ia/contexto", tags=["IA - Contexto Persistente"])


@router.get("/{proyecto_id}", response_model=ContextoIAResponse)
async def obtener_contexto_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector")),
) -> ContextoIAResponse:
    service = ContextoService(db)
    return await service.obtener_contexto(proyecto_id)


@router.post("/interaccion", response_model=ContextoIAResponse)
async def registrar_interaccion_ia(
    req: RegistrarInteraccionRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido()),
) -> ContextoIAResponse:
    await verificar_permiso(db, usuario, req.proyecto_id, "editor")
    service = ContextoService(db)
    return await service.registrar_interaccion(req)


@router.post("/snapshot", response_model=ContextoIAResponse)
async def guardar_snapshot_diagrama(
    req: GuardarSnapshotRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido()),
) -> ContextoIAResponse:
    await verificar_permiso(db, usuario, req.proyecto_id, "editor")
    service = ContextoService(db)
    return await service.guardar_snapshot(req)


@router.get("/{proyecto_id}/compilado", response_model=CompilarContextoResponse)
async def compilar_contexto_llm(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector")),
) -> CompilarContextoResponse:
    service = ContextoService(db)
    return await service.compilar_contexto(proyecto_id)


@router.post("/limpiar", response_model=ContextoIAResponse)
async def limpiar_memoria_contexto(
    req: LimpiarMemoriaRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido()),
) -> ContextoIAResponse:
    await verificar_permiso(db, usuario, req.proyecto_id, "anfitrion")
    service = ContextoService(db)
    return await service.limpiar_memoria(req)


# ─── Versiones del diagrama antes/después de cada interacción de la IA ──────

@router.get("/{proyecto_id}/versiones", response_model=VersionesPagina)
async def listar_versiones(
    proyecto_id: int,
    limite: int = Query(30, ge=1, le=100),
    antes_de_id: Optional[int] = Query(None, description="Paginación: versiones con id menor a este"),
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector")),
) -> VersionesPagina:
    """Historial completo (más reciente primero), sin el contenido del diagrama."""
    service = ContextoService(db)
    return await service.listar_versiones(proyecto_id, limite, antes_de_id)


@router.post("/{proyecto_id}/versiones", response_model=VersionResumen, status_code=201)
async def crear_version(
    proyecto_id: int,
    req: CrearVersionRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(requiere_proyecto("editor")),
) -> VersionResumen:
    """Versión de un cambio hecho sin la IA (o restauración). No modifica la memoria de la IA."""
    req.autor = usuario.nombre   # quién hizo el cambio lo dice la sesión, no el cliente
    service = ContextoService(db)
    return await service.crear_version(proyecto_id, req)


@router.get("/{proyecto_id}/versiones/{version_id}", response_model=VersionDetalle)
async def obtener_version(
    proyecto_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector")),
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
    usuario = Depends(requiere_proyecto("editor")),
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
    _ = Depends(requiere_proyecto("editor")),
) -> VersionResumen:
    """El frontend envía el diagrama tal como quedó después de aplicar el cambio de la IA."""
    service = ContextoService(db)
    return await service.guardar_version_despues(proyecto_id, version_id, req.estado_despues)


# ─── CU40: actividad y contribución por miembro ─────────────────────────────

@router.get("/{proyecto_id}/actividad")
async def actividad_por_miembro(
    proyecto_id: int,
    dias: Optional[int] = Query(30, ge=1, le=3650, description="Últimos N días; sin valor = todo"),
    todo: bool = Query(False, description="Ignorar 'dias' y contar todo el historial"),
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector")),
):
    from ..services.actividad_service import contribucion
    return await contribucion(db, proyecto_id, None if todo else dias)


# ─── Memoria del proyecto (estilo Engram) ───────────────────────────────────

@router.get("/{proyecto_id}/memorias", response_model=List[MemoriaItem])
async def listar_memorias(
    proyecto_id: int,
    incluir_historial: bool = Query(False, description="Incluir las observaciones reemplazadas"),
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector")),
) -> List[MemoriaItem]:
    return await ContextoService(db).listar_memorias(proyecto_id, incluir_historial)


@router.post("/{proyecto_id}/memorias", response_model=MemoriaItem, status_code=201)
async def crear_memoria(
    proyecto_id: int,
    req: CrearMemoriaRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("editor")),
) -> MemoriaItem:
    """Guardar algo a mano (también lo usa /recordar del chat)."""
    return await ContextoService(db).crear_memoria(proyecto_id, req)


@router.put("/{proyecto_id}/memorias/{memoria_id}", response_model=MemoriaItem)
async def editar_memoria(
    proyecto_id: int,
    memoria_id: int,
    req: EditarMemoriaRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("editor")),
) -> MemoriaItem:
    return await ContextoService(db).editar_memoria(proyecto_id, memoria_id, req)


@router.delete("/{proyecto_id}/memorias/{memoria_id}", status_code=204)
async def eliminar_memoria(
    proyecto_id: int,
    memoria_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("editor")),
) -> None:
    await ContextoService(db).eliminar_memoria(proyecto_id, memoria_id)


@router.post("/{proyecto_id}/memorias/{memoria_id}/resolver", response_model=MemoriaItem)
async def resolver_conflicto_memoria(
    proyecto_id: int,
    memoria_id: int,
    req: ResolverConflictoRequest,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("editor")),
) -> MemoriaItem:
    """Una memoria escrita a mano fue reemplazada por algo automático: elegir cuál vale."""
    return await ContextoService(db).resolver_conflicto_memoria(proyecto_id, memoria_id, req.mantener_nueva)
