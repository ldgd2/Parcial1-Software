import asyncio
import re
import unicodedata
from typing import Optional, Any
from .llm_client import consultar_llm, transcribir_audio, iniciar_medicion, hay_presupuesto
from .dsl_normalizer import normalize_ai_output, extraer_entidades_de_texto, garantizar_conectividad_relacional
from .prompt_compressor import HybridPromptCompressor


def deduplicar_resultado(resultado: dict) -> dict:
    """Elimina clases duplicadas por nombre y relaciones idénticas entre el mismo par de nodos."""
    nodes = resultado.get("nodes", [])
    seen_node_names = set()
    unique_nodes = []
    for n in nodes:
        name = str(n.get("name") or "").strip()
        lower = name.lower()
        if lower and lower not in seen_node_names:
            seen_node_names.add(lower)
            unique_nodes.append(n)
    resultado["nodes"] = unique_nodes

    relations = resultado.get("relations", [])
    seen_relations = set()
    unique_relations = []

    for r in relations:
        s_id = r.get("sourceId") or r.get("origen") or r.get("source")
        t_id = r.get("targetId") or r.get("destino") or r.get("target")
        rel_type = str(r.get("type") or "association").lower().strip()
        label = str(r.get("label") or "").strip()

        if not s_id or not t_id:
            continue

        pair_nodes = tuple(sorted([str(s_id).lower(), str(t_id).lower()]))
        rel_signature = (pair_nodes, rel_type, label)

        if rel_signature not in seen_relations:
            seen_relations.add(rel_signature)
            unique_relations.append(r)

    resultado["relations"] = unique_relations
    return resultado


# Encabezados que arma el chat para comandos que SÍ cambian el diagrama
_PEDIDOS_DE_CAMBIO = ("GENERAR DIAGRAMA", "REFACTORIZ", "REVISIÓN COMPLETA", "LIMPIEZA DE DIAGRAMA",
                      "DIAGRAMA DE", "SISTEMA DE", "MODELA")
# Verbos de cambio por raíz (sin acentos). No se usa el compresor: ahí "hace"/"hacia" cuentan como ADD.
_VERBO_DE_CAMBIO = re.compile(
    r"\b(agreg|anad|crea|crear|cree|incluy|insert|elimin|borr|quit|remuev|remov|modific|cambi|renombr|"
    r"edit|actualiz|conect|relacion[ae]|vincul|asoci[ae]|un[ea]\b|corrig|correg|arregl|repar|solucion|"
    r"normaliz|refactoriz|genera|disen|separ|divid|fusion|mueve|muev|convierte|convert|reemplaz|ajust)\w*",
)


def _sin_acentos(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()


def _pide_cambios(prompt: str) -> bool:
    """¿El pedido es para crear/cambiar el diagrama? (preguntas y explicaciones no)."""
    if any(p in (prompt or "").upper() for p in _PEDIDOS_DE_CAMBIO):
        return True
    return bool(_VERBO_DE_CAMBIO.search(_sin_acentos(prompt)))


def _tiene_cambios(resultado: dict) -> bool:
    return bool(
        resultado.get("nodes") or resultado.get("relations")
        or resultado.get("deletedNodes") or resultado.get("deletedRelations")
        or resultado.get("tasks")
    )


async def generar_diagrama_desde_prompt(
    prompt: str,
    context: Optional[str] = None,
    image_base64: Optional[str] = None,
    image_mime_type: str = "image/png",
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    db: Optional[Any] = None,
    estado_antes: Optional[dict] = None,
    autor: Optional[str] = None,
    cancelado: Optional[Any] = None,
    correcciones: Optional[list] = None
) -> dict:
    """
    Orquestador único y genérico para generación/refactorización de diagramas UML.
    1. Integra memoria persistente comprimida si se proporciona proyecto_id y sesión de BD.
    2. Invoca el cliente LLM universal con el prompt de sistema estándar.
    3. Normaliza el resultado a través de dsl_normalizer (garantía relacional, sin huérfanas).
    4. Si el modelo devuelve solo prosa o array de nodos vacío, ejecuta fallback automático a Gemini
       y/o sintetizador de entidades de dominio para garantizar que el lienzo NUNCA quede vacío.
    5. Persiste el nuevo estado cognitivo ahorrando tokens.
    """
    effective_context = context or ""
    uso = iniciar_medicion()   # tokens reales de este pedido (todas las llamadas que haga)

    if db is not None and proyecto_id is not None and proyecto_id > 0:
        try:
            from backend.modules.gestion_asistencia_ia.gestionar_contexto_persistente.services.contexto_service import ContextoService
            service = ContextoService(db)
            if correcciones is not None:
                # las correcciones del diagrama entran a la memoria ANTES de armar el contexto
                await service.sincronizar_correcciones(proyecto_id, correcciones)
            compilado = await service.compilar_contexto(proyecto_id, consulta=prompt, incluir_diagrama=not context)
            if compilado and compilado.contexto_compilado_llm:
                effective_context = (
                    f"{compilado.contexto_compilado_llm}\n\nDiagrama actual (en vivo):\n{context}"
                    if context else compilado.contexto_compilado_llm
                )
        except Exception as ctx_err:
            print(f"[ContextoPersistente] Advertencia al compilar memoria: {ctx_err}")

    # Se envía el pedido ORIGINAL: comprimirlo (minúsculas, sin acentos, verbos → ADD/EDIT…) cambiaba
    # los nombres de clases y atributos ("MétodoPago" → "metodopago") y ahorraba muy pocos tokens.
    # La compresión se sigue usando solo para guardar el historial en la memoria.
    prompt_to_send = prompt
    rescatar = bool(image_base64) or _pide_cambios(prompt)   # una imagen siempre es para digitalizar

    raw_response, used_provider = await consultar_llm(
        prompt=prompt_to_send,
        context=effective_context if effective_context else None,
        image_base64=image_base64,
        image_mime_type=image_mime_type,
        provider=provider,
        api_key=api_key
    )

    resultado = normalize_ai_output(raw_response, context=effective_context)
    resultado["provider_used"] = used_provider

    # Rescates SOLO si se pidió cambiar el diagrama y la respuesta no trae ningún cambio.
    # (Antes también corrían con una respuesta que solo borraba o solo traía tareas, y con preguntas:
    #  la IA respondía en prosa y se "extraían" clases inventadas como propuesta.)
    rescatar = rescatar and not _tiene_cambios(resultado)

    # Rescate nivel 1: recurrir a Gemini con la llave del SERVIDOR (la del usuario es de otro proveedor)
    # used_provider puede ser "gemini (fallback)": antes se volvía a llamar a Gemini con el mismo pedido
    if rescatar and hay_presupuesto() and not used_provider.startswith("gemini"):
        try:
            from .llm_client import _consultar_gemini
            fb_raw = await _consultar_gemini(prompt_to_send, context=effective_context, api_key=None)
            fb_res = normalize_ai_output(fb_raw, context=effective_context)
            if fb_res.get("nodes") and len(fb_res["nodes"]) > 0:
                resultado = fb_res
                resultado["provider_used"] = "gemini (fallback)"
        except Exception as fb_err:
            print(f"[PromptService] Fallback automático a Gemini falló: {fb_err}")

    # Rescate nivel 2: Si aún no hay clases, probar OpenRouter
    if rescatar and hay_presupuesto() and not _tiene_cambios(resultado) and not resultado.get("provider_used", "").startswith("openrouter"):
        try:
            from .llm_client import _consultar_openrouter
            fb_raw = await _consultar_openrouter(prompt_to_send, context=effective_context, api_key=None)
            fb_res = normalize_ai_output(fb_raw, context=effective_context)
            if fb_res.get("nodes") and len(fb_res["nodes"]) > 0:
                resultado = fb_res
                resultado["provider_used"] = "openrouter (fallback)"
        except Exception as fb_err2:
            print(f"[PromptService] Fallback automático a OpenRouter falló: {fb_err2}")

    # Rescate nivel 3: Si la respuesta fue en prosa y describe entidades, extraerlas limpiamente
    if rescatar and not _tiene_cambios(resultado):
        extracted = extraer_entidades_de_texto(f"{resultado.get('summary') or ''} {raw_response}")
        if extracted:
            resultado["nodes"] = extracted
            resultado["relations"] = garantizar_conectividad_relacional(extracted, resultado.get("relations") or [])
            if not resultado.get("summary"):
                resultado["summary"] = "Entidades extraídas y conectadas coherentemente."

    # Si el usuario pulsó "Detener" mientras la IA pensaba, no se registra nada
    if cancelado is not None:
        try:
            if await cancelado():
                return resultado
        except Exception:
            pass

    if db is not None and proyecto_id is not None and proyecto_id > 0:
        try:
            from backend.modules.gestion_asistencia_ia.gestionar_contexto_persistente.services.contexto_service import ContextoService
            from backend.modules.gestion_asistencia_ia.gestionar_contexto_persistente.schemas.request import RegistrarInteraccionRequest
            service = ContextoService(db)
            # La respuesta queda como propuesta pendiente si cambia el diagrama
            hay_cambios = _tiene_cambios(resultado)
            propuesta = {
                "nodes": resultado.get("nodes") or [],
                "relations": resultado.get("relations") or [],
                "deletedNodes": resultado.get("deletedNodes") or [],
                "deletedRelations": resultado.get("deletedRelations") or [],
                "tasks": resultado.get("tasks") or [],
                "summary": resultado.get("summary") or "",
            } if hay_cambios else None
            # shield: una vez empezado, el registro termina aunque se cancele la petición (no queda a medias)
            registro = await asyncio.shield(service.registrar_interaccion(
                RegistrarInteraccionRequest(
                    proyecto_id=proyecto_id,
                    user_prompt=prompt,
                    ai_summary=resultado.get("summary"),
                    added_nodes=[n.get("name") for n in resultado.get("nodes", []) if n.get("name")],
                    deleted_nodes=resultado.get("deletedNodes") or [],
                    diagram_dsl=context or "",
                    estado_antes=estado_antes,
                    autor=autor,
                    propuesta=propuesta,
                )
            ))
            resultado["version_id"] = registro.version_id
        except Exception as reg_err:
            print(f"[ContextoPersistente] Advertencia al persistir interacción: {reg_err}")

    final = deduplicar_resultado(resultado)
    final["uso_tokens"] = dict(uso)
    print(f"[IA] pedido proyecto={proyecto_id}: {uso['llamadas']} llamada(s), "
          f"{uso['entrada']} tokens de entrada, {uso['salida']} de salida ({', '.join(uso['proveedores'])})")
    return final


async def transcribe_audio_with_gemini(
    base64_audio: str,
    mime_type: str = "audio/webm",
    api_key: Optional[str] = None
) -> str:
    """Transcribe audio de micrófono utilizando el gateway unificado de IA."""
    return await transcribir_audio(base64_audio, mime_type, api_key)
