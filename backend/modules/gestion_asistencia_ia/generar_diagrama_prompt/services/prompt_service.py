from typing import Optional, Any
from .llm_client import consultar_llm, transcribir_audio
from .dsl_normalizer import normalize_ai_output


def deduplicar_resultado(resultado: dict) -> dict:
    """Elimina relaciones idénticas (mismo tipo y label) entre el mismo par de nodos."""
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

        pair_nodes = tuple(sorted([str(s_id), str(t_id)]))
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
    4. Persiste el nuevo estado cognitivo ahorrando tokens.
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

    raw_response, used_provider = await consultar_llm(
        prompt=prompt,
        context=effective_context if effective_context else None,
        image_base64=image_base64,
        image_mime_type=image_mime_type,
        provider=provider,
        api_key=api_key
    )

    resultado = normalize_ai_output(raw_response, context=effective_context)
    resultado["provider_used"] = used_provider

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
