from typing import Optional, Any
from .llm_client import consultar_llm, transcribir_audio
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


async def generar_diagrama_desde_prompt(
    prompt: str,
    context: Optional[str] = None,
    image_base64: Optional[str] = None,
    image_mime_type: str = "image/png",
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    db: Optional[Any] = None
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

    if db is not None and proyecto_id is not None and proyecto_id > 0:
        try:
            from backend.modules.gestion_asistencia_ia.gestionar_contexto_persistente.services.contexto_service import ContextoService
            service = ContextoService(db)
            compilado = await service.compilar_contexto(proyecto_id)
            if compilado and compilado.contexto_compilado_llm:
                effective_context = f"{compilado.contexto_compilado_llm}\n\nLienzo Actual:\n{effective_context}"
        except Exception as ctx_err:
            print(f"[ContextoPersistente] Advertencia al compilar memoria: {ctx_err}")

    compressor = HybridPromptCompressor()
    compressed_prompt = compressor.compress(prompt) if not image_base64 else prompt
    prompt_to_send = compressed_prompt if compressed_prompt and len(compressed_prompt) >= 4 else prompt

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

    # Rescate nivel 1: Si el proveedor no generó clases, recurrir inmediatamente a Gemini
    if (not resultado.get("nodes") or len(resultado["nodes"]) == 0) and used_provider != "gemini":
        try:
            from .llm_client import _consultar_gemini
            fb_raw = await _consultar_gemini(prompt_to_send, context=effective_context, api_key=api_key)
            fb_res = normalize_ai_output(fb_raw, context=effective_context)
            if fb_res.get("nodes") and len(fb_res["nodes"]) > 0:
                resultado = fb_res
                resultado["provider_used"] = "gemini (fallback)"
        except Exception as fb_err:
            print(f"[PromptService] Fallback automático a Gemini falló: {fb_err}")

    # Rescate nivel 2: Si aún no hay clases, probar OpenRouter
    if (not resultado.get("nodes") or len(resultado["nodes"]) == 0) and used_provider != "openrouter":
        try:
            from .llm_client import _consultar_openrouter
            fb_raw = await _consultar_openrouter(prompt_to_send, context=effective_context, api_key=api_key)
            fb_res = normalize_ai_output(fb_raw, context=effective_context)
            if fb_res.get("nodes") and len(fb_res["nodes"]) > 0:
                resultado = fb_res
                resultado["provider_used"] = "openrouter (fallback)"
        except Exception as fb_err2:
            print(f"[PromptService] Fallback automático a OpenRouter falló: {fb_err2}")

    # Rescate nivel 3: Si la respuesta fue en prosa y describe entidades, extraerlas limpiamente
    if not resultado.get("nodes") or len(resultado["nodes"]) == 0:
        extracted = extraer_entidades_de_texto(f"{resultado.get('summary') or ''} {raw_response}")
        if extracted:
            resultado["nodes"] = extracted
            resultado["relations"] = garantizar_conectividad_relacional(extracted, resultado.get("relations") or [])
            if not resultado.get("summary"):
                resultado["summary"] = "Entidades extraídas y conectadas coherentemente."

    if db is not None and proyecto_id is not None and proyecto_id > 0:
        try:
            from backend.modules.gestion_asistencia_ia.gestionar_contexto_persistente.services.contexto_service import ContextoService
            from backend.modules.gestion_asistencia_ia.gestionar_contexto_persistente.schemas.request import RegistrarInteraccionRequest
            service = ContextoService(db)
            await service.registrar_interaccion(
                RegistrarInteraccionRequest(
                    proyecto_id=proyecto_id,
                    user_prompt=prompt,
                    ai_summary=resultado.get("summary"),
                    added_nodes=[n.get("name") for n in resultado.get("nodes", []) if n.get("name")],
                    deleted_nodes=resultado.get("deletedNodes") or [],
                    diagram_dsl=context or ""
                )
            )
        except Exception as reg_err:
            print(f"[ContextoPersistente] Advertencia al persistir interacción: {reg_err}")

    return deduplicar_resultado(resultado)


async def transcribe_audio_with_gemini(
    base64_audio: str,
    mime_type: str = "audio/webm",
    api_key: Optional[str] = None
) -> str:
    """Transcribe audio de micrófono utilizando el gateway unificado de IA."""
    return await transcribir_audio(base64_audio, mime_type, api_key)
