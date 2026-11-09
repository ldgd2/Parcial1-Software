import time
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..repositories.contexto_repository import ContextoRepository
from ..schemas.request import (
    RegistrarInteraccionRequest,
    GuardarSnapshotRequest,
    LimpiarMemoriaRequest,
    CrearVersionRequest,
    DecidirPropuestaRequest,
    CrearMemoriaRequest,
    EditarMemoriaRequest,
)
from ..schemas.response import (
    ContextoIAResponse,
    CompilarContextoResponse,
    EventoEpisodico,
    CorreccionItem,
    MemoriaSecciones,
    VersionDetalle,
    VersionResumen,
    VersionesPagina,
    MemoriaItem,
)
from . import memoria_service
from .memory_compressor_service import (
    comprimir_instruccion,
    generar_delta_compacto,
    compilar_contexto_para_llm,
    detectar_dominio,
    secciones_contexto,
)

# Eventos que se conservan en la memoria del prompt (control de tokens).
# El historial completo con versiones vive en `versiones_contexto_ia`.
MAX_EVENTOS_MEMORIA = 15


def _compilar(contexto, memorias=None):
    return compilar_contexto_para_llm(
        proyecto_id=contexto.proyecto_id,
        dominio=contexto.dominio,
        resumen_acumulado=contexto.resumen_acumulado,
        historial=contexto.historial_comprimido,
        correcciones=contexto.correcciones,
        snapshot_dsl=contexto.snapshot_dsl,
        memorias=memorias,
    )


def _secciones(contexto, memorias=None) -> MemoriaSecciones:
    return MemoriaSecciones(**secciones_contexto(
        dominio=contexto.dominio,
        resumen_acumulado=contexto.resumen_acumulado,
        historial=contexto.historial_comprimido,
        correcciones=contexto.correcciones,
        snapshot_dsl=contexto.snapshot_dsl,
        memorias=memorias,
    ))


def _respuesta(contexto, bloque: Optional[str] = None, version_id: Optional[int] = None, memorias=None) -> ContextoIAResponse:
    if bloque is None:
        bloque, _, _ = _compilar(contexto, memorias)
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
        fecha_actualizacion=contexto.fecha_actualizacion.isoformat() if contexto.fecha_actualizacion else None,
        memoria_secciones=_secciones(contexto, memorias),
        version_id=version_id,
    )


def _version_resumen(v) -> Dict[str, Any]:
    return dict(
        id=v.id,
        ts=v.ts,
        intent=v.intent,
        cmd=v.cmd,
        resumen=v.resumen,
        delta=v.delta,
        autor=v.autor,
        tiene_antes=v.estado_antes is not None,
        tiene_despues=v.estado_despues is not None,
        estado_propuesta=v.estado_propuesta,
        decidida_por=v.decidida_por,
        decidida_en=int(v.decidida_en.timestamp()) if v.decidida_en else None,
    )


class ContextoService:
    def __init__(self, db: AsyncSession):
        self.repo = ContextoRepository(db)

    async def _memorias(self, proyecto_id: int, consulta: str = ""):
        filas = await memoria_service.buscar_relevantes(self.repo.db, proyecto_id, consulta)
        return [memoria_service.a_dict(m) for m in filas]

    async def obtener_contexto(self, proyecto_id: int) -> ContextoIAResponse:
        contexto = await self.repo.create_or_get(proyecto_id)
        return _respuesta(contexto, memorias=await self._memorias(proyecto_id))

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
        ts = int(time.time())
        nuevo_evento = {
            "ts": ts,
            "intent": req.intent or "GENERAL",
            "cmd": cmd_comprimido,
            "delta": delta_str,
            "summary": (req.ai_summary or "Acción ejecutada con éxito.")[:100]
        }

        # Mantener solo las últimas interacciones para control estricto de memoria
        historial = list(contexto.historial_comprimido)
        historial.append(nuevo_evento)
        if len(historial) > MAX_EVENTOS_MEMORIA:
            historial = historial[-MAX_EVENTOS_MEMORIA:]
        contexto.historial_comprimido = historial

        # 4. Actualizar correcciones activas si se proporcionaron
        if req.correcciones is not None:
            corrs = [c.model_dump() for c in req.correcciones]
            contexto.correcciones = corrs

        # 5. Actualizar snapshot DSL si se incluyó
        if req.diagram_dsl:
            contexto.snapshot_dsl = req.diagram_dsl.strip()

        # 6. Actualizar resumen acumulado (acumula; antes se pisaba con el último resumen)
        if req.ai_summary:
            contexto.resumen_acumulado = memoria_service.acumular_resumen(
                contexto.resumen_acumulado, req.ai_summary.strip()
            )

        # 7. Compilar contexto para LLM y recalcular métricas de tokens
        bloque, _, tokens_ahorrados = _compilar(contexto)
        contexto.tokens_ahorrados_estimados += tokens_ahorrados

        # 8. Historial completo con la versión del diagrama antes/después
        #    (se confirma junto con el contexto en `update()`)
        version = await self.repo.agregar_version(
            proyecto_id=req.proyecto_id,
            ts=ts,
            intent=nuevo_evento["intent"],
            cmd=req.user_prompt.strip()[:2000],
            resumen=(req.ai_summary or "").strip()[:2000],
            delta=delta_str,
            autor=(req.autor or None),
            estado_antes=req.estado_antes,
            estado_despues=req.estado_despues,
            propuesta=req.propuesta,
            estado_propuesta="pendiente" if req.propuesta else None,
        )
        version_id = version.id

        actualizado = await self.repo.update(contexto)
        return _respuesta(actualizado, bloque=bloque, version_id=version_id)

    async def sincronizar_correcciones(self, proyecto_id: int, correcciones: list) -> None:
        """Reemplaza las correcciones de la memoria por las del diagrama (las abiertas llegan al prompt)."""
        contexto = await self.repo.create_or_get(proyecto_id)
        limpias = []
        for c in (correcciones or [])[:50]:
            texto = str(c.get("text") or c.get("texto") or "").strip()
            if not texto:
                continue
            limpias.append({
                "id": str(c.get("id") or len(limpias) + 1)[:64],
                "target": str(c.get("target") or "General")[:120],
                "text": texto[:300],
                "estado": "resuelta" if c.get("estado") == "resuelta" else "abierta",
            })
        if limpias != list(contexto.correcciones or []):
            contexto.correcciones = limpias
            await self.repo.update(contexto)

    async def guardar_snapshot(self, req: GuardarSnapshotRequest) -> ContextoIAResponse:
        contexto = await self.repo.create_or_get(req.proyecto_id)
        contexto.snapshot_dsl = req.diagram_dsl.strip()
        if req.dominio:
            contexto.dominio = req.dominio
        if req.resumen_acumulado:
            contexto.resumen_acumulado = req.resumen_acumulado.strip()

        actualizado = await self.repo.update(contexto)
        return _respuesta(actualizado)

    async def compilar_contexto(self, proyecto_id: int, consulta: str = "") -> CompilarContextoResponse:
        """`consulta` es el pedido actual: se usa para elegir las memorias relevantes."""
        contexto = await self.repo.create_or_get(proyecto_id)
        memorias = await self._memorias(proyecto_id, consulta)
        bloque, tokens_est, tokens_ahor = _compilar(contexto, memorias)

        abiertas_count = sum(1 for c in contexto.correcciones if c.get("estado") == "abierta")

        return CompilarContextoResponse(
            proyecto_id=proyecto_id,
            contexto_compilado_llm=bloque,
            tokens_estimados=tokens_est,
            tokens_ahorrados=tokens_ahor,
            total_eventos_recordados=len(contexto.historial_comprimido),
            correcciones_activas_count=abiertas_count,
            memoria_secciones=_secciones(contexto, memorias),
        )

    async def limpiar_memoria(self, req: LimpiarMemoriaRequest) -> ContextoIAResponse:
        # Reinicia la memoria del prompt. El historial de versiones se conserva:
        # es el registro de lo que pasó en el diagrama, no memoria de la IA.
        contexto = await self.repo.reset(req.proyecto_id, conservar_dominio=req.conservar_dominio)
        if not contexto:
            raise HTTPException(status_code=404, detail="Contexto no encontrado para este proyecto")
        return _respuesta(contexto)

    # ─── Versiones ──────────────────────────────────────────────────────────

    async def listar_versiones(
        self, proyecto_id: int, limite: int = 30, antes_de_id: Optional[int] = None
    ) -> VersionesPagina:
        limite = max(1, min(limite, 100))
        filas = await self.repo.listar_versiones(proyecto_id, limite, antes_de_id)
        hay_mas = len(filas) > limite
        return VersionesPagina(
            items=[VersionResumen(**_version_resumen(v)) for v in filas[:limite]],
            hay_mas=hay_mas,
        )

    async def crear_version(self, proyecto_id: int, req: CrearVersionRequest) -> VersionResumen:
        """Registra una versión sin tocar la memoria de la IA (p. ej. cambios manuales)."""
        v = await self.repo.crear_version(
            proyecto_id=proyecto_id,
            ts=int(time.time()),
            intent=(req.intent or "MANUAL").upper(),
            cmd=req.cmd.strip(),
            resumen=req.resumen.strip(),
            delta=req.delta.strip(),
            autor=(req.autor or None),
            estado_antes=req.estado_antes,
            estado_despues=req.estado_despues,
            propuesta=req.propuesta,
            estado_propuesta="pendiente" if req.propuesta else None,
        )
        return VersionResumen(**_version_resumen(v))

    async def obtener_version(self, proyecto_id: int, version_id: int) -> VersionDetalle:
        v = await self.repo.obtener_version(proyecto_id, version_id)
        if not v:
            raise HTTPException(status_code=404, detail="Versión no encontrada")
        return VersionDetalle(
            **_version_resumen(v),
            estado_antes=v.estado_antes,
            estado_despues=v.estado_despues,
            propuesta=v.propuesta,
        )

    async def decidir_propuesta(
        self,
        proyecto_id: int,
        version_id: int,
        req: DecidirPropuestaRequest,
        usuario=None,
    ) -> VersionDetalle:
        """Aprueba o rechaza una propuesta pendiente y registra quién lo hizo."""
        v = await self.repo.obtener_version(proyecto_id, version_id)
        if not v:
            raise HTTPException(status_code=404, detail="Versión no encontrada")
        if v.estado_propuesta is None:
            raise HTTPException(status_code=400, detail="Esta versión no es una propuesta de la IA")

        por = getattr(usuario, "nombre", None) or (req.autor or None)
        por_id = getattr(usuario, "id", None)
        decidida = await self.repo.decidir_propuesta(
            proyecto_id, version_id,
            "aprobada" if req.aceptar else "rechazada",
            por, por_id,
            req.estado_antes if req.aceptar else None,
        )
        if decidida is None:
            actual = await self.repo.obtener_version(proyecto_id, version_id)
            await self.repo.db.refresh(actual)
            quien = actual.decidida_por or "otra persona"
            raise HTTPException(
                status_code=409,
                detail={
                    "mensaje": f"La propuesta ya fue {actual.estado_propuesta} por {quien}.",
                    "estado_propuesta": actual.estado_propuesta,
                    "decidida_por": actual.decidida_por,
                },
            )
        # CU39: avisar a quien pidió el cambio (el UPDATE atómico no pasa por los eventos del ORM)
        from backend.modules.gestion_notificaciones.services.notificaciones_service import programar
        programar([{"tipo": "propuesta_decidida", "proyecto_id": proyecto_id, "version_id": version_id,
                    "autor": decidida.autor, "por": por, "aprobada": req.aceptar,
                    "resumen": decidida.resumen or decidida.cmd}])
        # Memoria del proyecto: lo aprobado o rechazado se recuerda (no debe romper la decisión)
        try:
            await memoria_service.desde_propuesta(self.repo.db, decidida, req.aceptar, por)
        except Exception as e:
            await self.repo.db.rollback()
            print(f"[Memoria] No se pudo guardar la memoria de la propuesta {version_id}: {e}")
        return await self.obtener_version(proyecto_id, version_id)

    # ─── Memoria del proyecto (estilo Engram) ───────────────────────────────

    async def listar_memorias(self, proyecto_id: int, incluir_historial: bool = False) -> list:
        filas = await memoria_service.listar(self.repo.db, proyecto_id, incluir_historial)
        return [MemoriaItem(**memoria_service.a_dict(m)) for m in filas]

    async def crear_memoria(self, proyecto_id: int, req: CrearMemoriaRequest) -> MemoriaItem:
        if req.texto:
            datos = memoria_service.desde_texto(req.texto)
        else:
            if not (req.que or req.titulo):
                raise HTTPException(status_code=400, detail="Escribe qué hay que recordar")
            datos = dict(
                tipo=req.tipo or "convencion",
                topic_key=req.topic_key or f"notas/{memoria_service.slug(req.titulo or req.que, 40)}",
                titulo=req.titulo or (req.que or "")[:80],
                que=req.que or req.titulo or "",
                por_que=req.por_que or "", donde=req.donde or "", aprendido=req.aprendido or "",
            )
        m = await memoria_service.guardar(self.repo.db, proyecto_id, origen="manual", autor=req.autor, **datos)
        return MemoriaItem(**memoria_service.a_dict(m))

    async def editar_memoria(self, proyecto_id: int, memoria_id: int, req: EditarMemoriaRequest) -> MemoriaItem:
        m = await memoria_service.obtener(self.repo.db, proyecto_id, memoria_id)
        if not m:
            raise HTTPException(status_code=404, detail="Memoria no encontrada")
        m = await memoria_service.editar(self.repo.db, m, req.model_dump())
        return MemoriaItem(**memoria_service.a_dict(m))

    async def eliminar_memoria(self, proyecto_id: int, memoria_id: int) -> None:
        m = await memoria_service.obtener(self.repo.db, proyecto_id, memoria_id)
        if not m:
            raise HTTPException(status_code=404, detail="Memoria no encontrada")
        await memoria_service.eliminar(self.repo.db, m)

    async def resolver_conflicto_memoria(self, proyecto_id: int, memoria_id: int, mantener_nueva: bool) -> MemoriaItem:
        m = await memoria_service.obtener(self.repo.db, proyecto_id, memoria_id)
        if not m:
            raise HTTPException(status_code=404, detail="Memoria no encontrada")
        queda = await memoria_service.resolver_conflicto(self.repo.db, m, mantener_nueva)
        return MemoriaItem(**memoria_service.a_dict(queda))

    async def guardar_version_despues(
        self, proyecto_id: int, version_id: int, estado: Dict[str, Any]
    ) -> VersionResumen:
        v = await self.repo.obtener_version(proyecto_id, version_id)
        if not v:
            raise HTTPException(status_code=404, detail="Versión no encontrada")
        v = await self.repo.guardar_despues(v, estado)
        return VersionResumen(**_version_resumen(v))
