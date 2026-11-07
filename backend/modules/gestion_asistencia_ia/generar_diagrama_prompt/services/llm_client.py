import json
import re
from typing import Optional, Tuple
import httpx
from fastapi import HTTPException
from backend.core.config import settings

# ── PROMPT UNIVERSAL ÚNICO ESTRUCTURADO Y OPTIMIZADO (AGNOSTICO A DOMINIO) ──
UNIVERSAL_SYSTEM_PROMPT = (
    "Role: Senior Software & Database Architect. Language: SPANISH.\n"
    "Goal: Generate and refactor clean, logically-connected UML class diagrams for ANY software domain.\n\n"
    "CRITICAL RULES:\n"
    "1. USER-FACING SUMMARY (MANDATORY): 'summary' must be a concise (1-2 sentences) Spanish explanation of the entities, relationships, and changes made. Never mention internal terms.\n"
    "2. MANDATORY ENTITIES GENERATION: Always populate 'nodes' with complete domain classes (name in PascalCase, attributes with visibility and types like '+id:int', methods) and 'relations' with structural links. NEVER return empty 'nodes' on creation or refactoring requests.\n"
    "3. STRICT UML RELATIONSHIP CRITERIA (OBJECT-ORIENTED PRINCIPLES):\n"
    "   - 'association' (-): Default link between independent domain entities with separate lifecycles.\n"
    "   - 'aggregation' (o): Whole-part ('todo-parte débil') where the part can exist independently.\n"
    "   - 'composition' (*): Strong whole-part ('todo-parte fuerte') where the child cannot exist without the parent (cascade delete).\n"
    "   - 'inheritance' (>): Strict 'is-a' specialization hierarchy only (e.g., Subtipo > Supertipo).\n"
    "   - 'dependency' (.): Uses-a / service reference.\n"
    "   - 'realization' (~): Implementation of an interface contract.\n"
    "   - Cardinalities: '1..*', '1:N', '1:1', 'N:M'.\n"
    "   - Endpoints: source and target must be exact class names.\n"
    "4. DELETIONS ('deletedNodes'): Include ONLY exact class names explicitly requested for removal or replaced. If none, return []. PROHIBIDO inventar nombres ficticios o cadenas genéricas como 'Node_x'.\n\n"
    "OUTPUT FORMAT: Return STRICT MINIFIED JSON ONLY:\n"
    "{\n"
    '  "nodes": [\n'
    '    {"name": "EntidadPrincipal", "type": "class", "attributes": ["+id:int", "+nombre:string", "+estado:string"], "methods": [".procesar():bool"]},\n'
    '    {"name": "EntidadSecundaria", "type": "class", "attributes": ["+id:int", "+*entidadPrincipal_id:FK"], "methods": []}\n'
    '  ],\n'
    '  "relations": [\n'
    '    {"source": "EntidadPrincipal", "target": "EntidadSecundaria", "type": "association", "label": "1..*"}\n'
    '  ],\n'
    '  "summary": "Diagrama estructurado según el dominio solicitado.",\n'
    '  "deletedNodes": []\n'
    "}"
)


def extraer_base64_imagen(raw_data: str, default_mime: str = "image/png") -> Tuple[str, str]:
    """Limpia y extrae (mime_type, base64_puro) de una imagen en base64."""
    clean = raw_data.strip()
    mime = default_mime
    if clean.startswith("data:"):
        parts = clean.split(",", 1)
        header = parts[0]
        clean = parts[1] if len(parts) > 1 else ""
        if "image/png" in header:
            mime = "image/png"
        elif "image/webp" in header:
            mime = "image/webp"
        elif "image/jpeg" in header or "image/jpg" in header:
            mime = "image/jpeg"
    elif "," in clean:
        clean = clean.split(",", 1)[1]
    return mime, clean


def limpiar_respuesta_llm(text: str) -> str:
    """Remueve bloques ``` o ```json o ```dsl preservando las líneas del Hyper-DSL."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


async def _consultar_gemini(
    prompt: str,
    context: Optional[str] = None,
    image_base64: Optional[str] = None,
    image_mime_type: str = "image/png",
    api_key: Optional[str] = None
) -> str:
    key = api_key or settings.GEMINI_API
    if not key:
        raise HTTPException(status_code=500, detail="API Key de Gemini no configurada en GEMINI_API")

    instruction_suffix = (
        "\n\n[INSTRUCCIÓN CRÍTICA DE SALIDA]: Devuelve EXCLUSIVAMENTE un objeto JSON válido "
        "con las claves 'nodes' (array de clases con name, type, attributes, methods), "
        "'relations' (array con source, target, type, label), 'summary' (resumen de 1-2 oraciones) y 'deletedNodes' ([]). "
        "PROHIBIDO responder solo con texto conversacional o explicaciones sin el JSON con 'nodes'."
    )
    full_prompt = prompt + instruction_suffix
    if context:
        full_prompt = f"Contexto Actual del Diagrama:\n{context}\n\nRequerimiento:\n{prompt}{instruction_suffix}"

    parts = [{"text": full_prompt}]
    if image_base64:
        mime, clean_b64 = extraer_base64_imagen(image_base64, image_mime_type)
        parts.append({"inlineData": {"mimeType": mime, "data": clean_b64}})

    payload = {
        "contents": [{"parts": parts}],
        "systemInstruction": {"parts": [{"text": UNIVERSAL_SYSTEM_PROMPT}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2,
            "maxOutputTokens": 8192
        }
    }

    models_to_try = ["gemini-2.5-flash"]
    last_error = ""

    async with httpx.AsyncClient(timeout=90.0) as client:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 404:
                    continue
                data = response.json()
                if response.status_code != 200:
                    last_error = f"HTTP {response.status_code}: {data}"
                    continue

                candidates = data.get("candidates", [])
                if not candidates:
                    last_error = "Sin candidatos válidos devueltos por Gemini"
                    continue

                raw_text = candidates[0]["content"]["parts"][0]["text"]
                return limpiar_respuesta_llm(raw_text)
            except httpx.RequestError as exc:
                last_error = str(exc)

    raise HTTPException(status_code=502, detail=f"Error consultando Gemini: {last_error}")


async def _consultar_kimi(
    prompt: str,
    context: Optional[str] = None,
    image_base64: Optional[str] = None,
    image_mime_type: str = "image/png",
    api_key: Optional[str] = None
) -> str:
    key = api_key or settings.KIMI_API
    instruction_suffix = (
        "\n\n[INSTRUCCIÓN CRÍTICA DE SALIDA]: Devuelve EXCLUSIVAMENTE un objeto JSON válido "
        "con las claves 'nodes' (array de clases con name, type, attributes, methods), "
        "'relations' (array con source, target, type, label), 'summary' (resumen de 1-2 oraciones) y 'deletedNodes' ([]). "
        "PROHIBIDO responder solo con texto conversacional o explicaciones sin el JSON con 'nodes'."
    )
    full_prompt = prompt + instruction_suffix
    if context:
        full_prompt = f"Contexto Actual del Diagrama:\n{context}\n\nRequerimiento:\n{prompt}{instruction_suffix}"

    user_content = []
    if image_base64:
        mime, clean_b64 = extraer_base64_imagen(image_base64, image_mime_type)
        user_content.append({"type": "text", "text": full_prompt})
        user_content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{clean_b64}"}})
    else:
        user_content = full_prompt

    last_error = ""

    # 1. Intentar endpoints oficiales directos de Moonshot (Kimi)
    if key:
        moonshot_headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        active_kimi_model = settings.KIMI_MODEL or "kimi-k3"
        moonshot_endpoints = [
            ("https://api.moonshot.ai/v1/chat/completions", "kimi-k3"),
            ("https://api.moonshot.ai/v1/chat/completions", active_kimi_model),
            ("https://api.moonshot.cn/v1/chat/completions", active_kimi_model),
            ("https://api.moonshot.cn/v1/chat/completions", "moonshot-v1-8k"),
        ]
        async with httpx.AsyncClient(timeout=120.0) as client:
            for url, model_name in moonshot_endpoints:
                temp = 1.0 if ("k3" in model_name.lower() or "kimi" in model_name.lower()) else 0.2
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": UNIVERSAL_SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    "temperature": temp,
                    "max_tokens": 8192
                }
                try:
                    response = await client.post(url, json=payload, headers=moonshot_headers)
                    if response.status_code == 200:
                        data = response.json()
                        msg = data["choices"][0]["message"]
                        content = msg.get("content") or ""
                        reasoning = msg.get("reasoning_content") or ""
                        raw = content if "{" in content else (reasoning if "{" in reasoning else (content or reasoning or ""))
                        cleaned = limpiar_respuesta_llm(raw)
                        if cleaned and len(cleaned) >= 15 and cleaned not in ["{", "{}", "[]", "null"]:
                            return cleaned
                    last_error = f"HTTP {response.status_code} ({model_name}): {response.text}"
                except httpx.RequestError as exc:
                    last_error = str(exc)

    raise HTTPException(status_code=502, detail=f"Error consultando Kimi API: {last_error}")


async def _consultar_openrouter(
    prompt: str,
    context: Optional[str] = None,
    image_base64: Optional[str] = None,
    image_mime_type: str = "image/png",
    api_key: Optional[str] = None
) -> str:
    key = api_key or settings.OPENROUTE_API
    if not key:
        raise HTTPException(status_code=500, detail="API Key de OpenRouter no configurada en OPENROUTE_API")

    instruction_suffix = (
        "\n\n[INSTRUCCIÓN CRÍTICA DE SALIDA]: Devuelve EXCLUSIVAMENTE un objeto JSON válido "
        "con las claves 'nodes' (array de clases con name, type, attributes, methods), "
        "'relations' (array con source, target, type, label), 'summary' (resumen de 1-2 oraciones) y 'deletedNodes' ([]). "
        "PROHIBIDO responder solo con texto conversacional o explicaciones sin el JSON con 'nodes'."
    )
    full_prompt = prompt + instruction_suffix
    if context:
        full_prompt = f"Contexto Actual:\n{context}\n\nRequerimiento:\n{prompt}{instruction_suffix}"

    model_name = settings.OPENROUTER_VISION_MODEL if image_base64 else (settings.OPENROUTER_MODEL or settings.IA_MODEL or "google/gemini-2.0-flash-exp:free")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://diagramador.gerlextech.com",
        "X-Title": "Diagramador UML Colaborativo"
    }

    user_content = []
    if image_base64:
        mime, clean_b64 = extraer_base64_imagen(image_base64, image_mime_type)
        user_content.append({"type": "text", "text": full_prompt})
        user_content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{clean_b64}"}})
    else:
        user_content = full_prompt

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": UNIVERSAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Error OpenRouter API ({response.status_code}): {response.text}")
            data = response.json()
            msg = data["choices"][0]["message"]
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning_content") or ""
            raw = content if "{" in content else (reasoning if "{" in reasoning else (content or reasoning or ""))
            cleaned = limpiar_respuesta_llm(raw)
            if not cleaned or len(cleaned) < 15 or cleaned in ["{", "{}", "[]", "null"]:
                raise HTTPException(status_code=502, detail="Respuesta truncada devuelta por OpenRouter")
            return cleaned
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error de red con OpenRouter: {exc}")


async def consultar_llm(
    prompt: str,
    context: Optional[str] = None,
    image_base64: Optional[str] = None,
    image_mime_type: str = "image/png",
    provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> Tuple[str, str]:
    """
    Punto de entrada genérico y único para invocar al proveedor de IA configurado.
    Soporta texto, contexto e imágenes base64 de manera unificada.
    """
    target = (provider or settings.AI_PROVIDER or "gemini").lower().strip()
    if target == "openroute":
        target = "openrouter"

    last_exc = None
    try:
        if target == "kimi":
            result = await _consultar_kimi(prompt, context, image_base64, image_mime_type, api_key)
            if result and len(result.strip()) >= 15 and result.strip() not in ["{", "{}", "[]", "null"]:
                return result, "kimi"
            raise ValueError("Kimi retornó respuesta insuficiente o vacía")
        elif target == "openrouter":
            result = await _consultar_openrouter(prompt, context, image_base64, image_mime_type, api_key)
            if result and len(result.strip()) >= 15 and result.strip() not in ["{", "{}", "[]", "null"]:
                return result, "openrouter"
            raise ValueError("OpenRouter retornó respuesta insuficiente o vacía")
        else:
            result = await _consultar_gemini(prompt, context, image_base64, image_mime_type, api_key)
            if result and len(result.strip()) >= 15 and result.strip() not in ["{", "{}", "[]", "null"]:
                return result, "gemini"
            raise ValueError("Gemini retornó respuesta insuficiente o vacía")
    except Exception as exc:
        last_exc = exc

    # Fallback automático a Gemini si el proveedor primario falla
    if target != "gemini" and settings.GEMINI_API:
        try:
            result = await _consultar_gemini(prompt, context, image_base64, image_mime_type)
            if result and len(result.strip()) >= 15 and result.strip() not in ["{", "{}", "[]", "null"]:
                return result, "gemini (fallback)"
        except Exception:
            pass

    if last_exc:
        raise last_exc
    raise HTTPException(status_code=500, detail="No se pudo obtener respuesta del proveedor de IA")


async def transcribir_audio(
    audio_base64: str,
    mime_type: str = "audio/webm",
    api_key: Optional[str] = None
) -> str:
    """Transcribe audio de micrófono a texto en español utilizando Gemini."""
    key = api_key or settings.GEMINI_API
    if not key:
        raise HTTPException(status_code=500, detail="API Key de Gemini no configurada para transcripción de audio")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": "Transcribe exactamente el siguiente audio en español. Solo devuelve el texto puro, sin explicaciones ni markdown."},
                {"inlineData": {"mimeType": mime_type, "data": audio_base64}}
            ]
        }],
        "generationConfig": {
            "temperature": 0.0
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            data = response.json()
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Error transcribiendo audio con Gemini")
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Error en transcripción de audio: {exc}")

