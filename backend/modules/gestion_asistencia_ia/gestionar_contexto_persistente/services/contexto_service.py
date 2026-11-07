import time
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..repositories.contexto_repository import ContextoRepository
from ..schemas.request import RegistrarInteraccionRequest, GuardarSnapshotRequest, LimpiarMemoriaRequest
from ..schemas.response import ContextoIAResponse, CompilarContextoResponse, EventoEpisodico, CorreccionItem
from .memory_compressor_service import (
    comprimir_instruccion,
    generar_delta_compacto,
    compilar_contexto_para_llm,
    detectar_dominio
)


class ContextoService:
    def __init__(self, db: AsyncSession):
        self.repo = ContextoRepository(db)

    async def obtener_contexto(self, proyecto_id: int) -> ContextoIAResponse:
        contexto = await self.repo.create_or_get(proyecto_id)
        bloque, _, _ = compilar_contexto_para_llm(
            proyecto_id=contexto.proyecto_id,
            dominio=contexto.dominio,
            resumen_acumulado=contexto.resumen_acumulado,
            historial=contexto.historial_comprimido,
            correcciones=contexto.correcciones,
            snapshot_dsl=contexto.snapshot_dsl
        )

        return ContextoIAResponse(
            id=contexto.id,
            proyecto_id=contexto.proyecto_id,
            dominio=contexto.dominio,
            resumen_acumulado=contexto.resumen_acumulado,
            historial_comprimido=[EventoEpisodico(**e) for e in contexto.historial_comprimido],
            correcciones=[CorreccionItem(**c) for c in contexto.correcciones],
            snapshot_dsl=contexto.snapshot_dsl,
            tokens_ahorrados_estimados=contexto.tokens_ahorrados_estimados,
            version=contexto.version,
            contexto_compilado_llm=bloque,
            fecha_actualizacion=contexto.fecha_actualizacion.isoformat() if contexto.fecha_actualizacion else None
        )

    async def registrar_interaccion(self, req: RegistrarInteraccionRequest) -> ContextoIAResponse:
        contexto = await self.repo.create_or_get(req.proyecto_id)

        # 1. Detectar y refinar dominio
        nuevo_dominio = detectar_dominio(
            texto=f"{req.user_prompt} {req.ai_summary or ''}",
            dominio_actual=contexto.dominio
        )
        contexto.dominio = nuevo_dominio

        # 2. Comprimir instrucción y generar delta
        cmd_comprimido = comprimir_instruccion(req.user_prompt)
        delta_str = generar_delta_compacto(
            added=req.added_nodes or [],
            updated=req.updated_nodes or [],
            deleted=req.deleted_nodes or []
        )

        # 3. Construir evento episódico ultra-comprimido
        nuevo_evento = {
            "ts": int(time.time()),
            "intent": req.intent or "GENERAL",
            "cmd": cmd_comprimido,
            "delta": delta_str,
            "summary": (req.ai_summary or "Acción ejecutada con éxito.")[:100]
        }

        # Mantener solo las últimas 15 interacciones para control estricto de memoria
        historial = list(contexto.historial_comprimido)
        historial.append(nuevo_evento)
        if len(historial) > 15:
            historial = historial[-15:]
        contexto.historial_comprimido = historial

        # 4. Actualizar correcciones activas si se proporcionaron
        if req.correcciones is not None:
            corrs = [c.model_dump() for c in req.correcciones]
            contexto.correcciones = corrs

        # 5. Actualizar snapshot DSL si se incluyó
        if req.diagram_dsl:
            contexto.snapshot_dsl = req.diagram_dsl.strip()

        # 6. Actualizar resumen acumulado
        if req.ai_summary:
            contexto.resumen_acumulado = req.ai_summary.strip()

        # 7. Compilar contexto para LLM y recalcular métricas de tokens
        bloque, _, tokens_ahorrados = compilar_contexto_para_llm(
            proyecto_id=contexto.proyecto_id,
            dominio=contexto.dominio,
            resumen_acumulado=contexto.resumen_acumulado,
            historial=contexto.historial_comprimido,
            correcciones=contexto.correcciones,
            snapshot_dsl=contexto.snapshot_dsl
        )
        contexto.tokens_ahorrados_estimados += tokens_ahorrados

        actualizado = await self.repo.update(contexto)

        return ContextoIAResponse(
            id=actualizado.id,
            proyecto_id=actualizado.proyecto_id,
            dominio=actualizado.dominio,
            resumen_acumulado=actualizado.resumen_acumulado,
            historial_comprimido=[EventoEpisodico(**e) for e in actualizado.historial_comprimido],
            correcciones=[CorreccionItem(**c) for c in actualizado.correcciones],
            snapshot_dsl=actualizado.snapshot_dsl,
            tokens_ahorrados_estimados=actualizado.tokens_ahorrados_estimados,
            version=actualizado.version,
            contexto_compilado_llm=bloque,
            fecha_actualizacion=actualizado.fecha_actualizacion.isoformat() if actualizado.fecha_actualizacion else None
        )

    async def guardar_snapshot(self, req: GuardarSnapshotRequest) -> ContextoIAResponse:
        contexto = await self.repo.create_or_get(req.proyecto_id)
        contexto.snapshot_dsl = req.diagram_dsl.strip()
        if req.dominio:
            contexto.dominio = req.dominio
        if req.resumen_acumulado:
            contexto.resumen_acumulado = req.resumen_acumulado.strip()

        actualizado = await self.repo.update(contexto)
        bloque, _, _ = compilar_contexto_para_llm(
            proyecto_id=actualizado.proyecto_id,
            dominio=actualizado.dominio,
            resumen_acumulado=actualizado.resumen_acumulado,
            historial=actualizado.historial_comprimido,
            correcciones=actualizado.correcciones,
            snapshot_dsl=actualizado.snapshot_dsl
        )

        return ContextoIAResponse(
            id=actualizado.id,
            proyecto_id=actualizado.proyecto_id,
            dominio=actualizado.dominio,
            resumen_acumulado=actualizado.resumen_acumulado,
            historial_comprimido=[EventoEpisodico(**e) for e in actualizado.historial_comprimido],
            correcciones=[CorreccionItem(**c) for c in actualizado.correcciones],
            snapshot_dsl=actualizado.snapshot_dsl,
            tokens_ahorrados_estimados=actualizado.tokens_ahorrados_estimados,
            version=actualizado.version,
            contexto_compilado_llm=bloque,
            fecha_actualizacion=actualizado.fecha_actualizacion.isoformat() if actualizado.fecha_actualizacion else None
        )

    async def compilar_contexto(self, proyecto_id: int) -> CompilarContextoResponse:
        contexto = await self.repo.create_or_get(proyecto_id)
        bloque, tokens_est, tokens_ahor = compilar_contexto_para_llm(
            proyecto_id=contexto.proyecto_id,
            dominio=contexto.dominio,
            resumen_acumulado=contexto.resumen_acumulado,
            historial=contexto.historial_comprimido,
            correcciones=contexto.correcciones,
            snapshot_dsl=contexto.snapshot_dsl
        )

        abiertas_count = sum(1 for c in contexto.correcciones if c.get("estado") == "abierta")

        return CompilarContextoResponse(
            proyecto_id=proyecto_id,
            contexto_compilado_llm=bloque,
            tokens_estimados=tokens_est,
            tokens_ahorrados=tokens_ahor,
            total_eventos_recordados=len(contexto.historial_comprimido),
            correcciones_activas_count=abiertas_count
        )

    async def limpiar_memoria(self, req: LimpiarMemoriaRequest) -> ContextoIAResponse:
        contexto = await self.repo.reset(req.proyecto_id, conservar_dominio=req.conservar_dominio)
        if not contexto:
            raise HTTPException(status_code=404, detail="Contexto no encontrado para este proyecto")

        bloque, _, _ = compilar_contexto_para_llm(
            proyecto_id=contexto.proyecto_id,
            dominio=contexto.dominio,
            resumen_acumulado=contexto.resumen_acumulado,
            historial=contexto.historial_comprimido,
            correcciones=contexto.correcciones,
            snapshot_dsl=contexto.snapshot_dsl
        )

        return ContextoIAResponse(
            id=contexto.id,
            proyecto_id=contexto.proyecto_id,
            dominio=contexto.dominio,
            resumen_acumulado=contexto.resumen_acumulado,
            historial_comprimido=[],
            correcciones=[],
            snapshot_dsl="",
            tokens_ahorrados_estimados=contexto.tokens_ahorrados_estimados,
            version=contexto.version,
            contexto_compilado_llm=bloque,
            fecha_actualizacion=contexto.fecha_actualizacion.isoformat() if contexto.fecha_actualizacion else None
        )

