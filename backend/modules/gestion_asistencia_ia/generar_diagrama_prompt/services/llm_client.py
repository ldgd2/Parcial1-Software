import json
import re
from typing import Optional, Tuple
import httpx
from fastapi import HTTPException
from backend.core.config import settings

# ── PROMPT UNIVERSAL ÚNICO ESTRUCTURADO Y OPTIMIZADO ────────────────────────
UNIVERSAL_SYSTEM_PROMPT = (
    "Role: Senior Software & Database Architect. Language: SPANISH.\n"
    "Goal: Generate and refactor clean, logically-connected UML class diagrams for software & university systems.\n\n"
    "CRITICAL ARCHITECTURAL RULES:\n"
    "1. USER-FACING SUMMARY (MANDATORY): 'summary' must be a clear, human-friendly explanation in Spanish for the user describing the entities, connections, and improvements made. NEVER mention internal terms like 'Hyper-DSL'.\n"
    "2. PURGE OBSOLETE & JUNK (MANDATORY): Always populate 'deletedNodes' array with any junk, temporary, or English classes (e.g., [\"Node_x\", \"Node_1\", \"Node_2\", \"Node_3\", \"Node_4\", \"Student\", \"Grade\", \"Course\", \"Instructor\", \"Assignment\", \"Task\", \"Submission\", \"Review\", \"Feedback\", \"Notification\", \"Diagrama\", \"eliminadas\", \"borradas\"]).\n"
    "   PROHIBITED: NEVER create classes named 'Diagrama', 'eliminadas', 'borradas', 'clases', 'nodo', or sentences. 'deletedNodes' is strictly a list of class names to remove.\n"
    "3. REAL DOMAIN ENTITIES (SPANISH PASCALCASE): Model complete domain entities:\n"
    "   - Usuario (id:int, nombre:string, email:string, password:string, rol:string)\n"
    "   - Docente (hereda de Usuario con 'inheritance' >): especialidad:string, departamento:string\n"
    "   - Estudiante (hereda de Usuario con 'inheritance' >): matricula:string, carrera:string, semestre:int\n"
    "   - Materia: codigo:string, nombre:string, creditos:int\n"
    "   - Curso: gestion:int, semestre:string, aula:string (*docente_id:FK, *materia_id:FK)\n"
    "   - Inscripcion: fecha:date, estado:string (*estudiante_id:FK, *curso_id:FK)\n"
    "   - Tarea: titulo:string, descripcion:string, fechaLimite:date, ponderacion:float (*curso_id:FK)\n"
    "   - Entrega: archivo:string, fechaEnvio:datetime, estado:string (*tarea_id:FK, *estudiante_id:FK)\n"
    "   - Calificacion: nota:float, observaciones:string, estado:string (*entrega_id:FK, *inscripcion_id:FK)\n"
    "   - Revision: fecha:date, comentarios:string, puntaje:float (*entrega_id:FK, *docente_id:FK)\n"
    "   - Comentario: texto:string, fecha:datetime (*revision_id:FK)\n"
    "   - Notificacion: mensaje:string, fecha:datetime, leido:bool (*usuario_id:FK)\n"
    "4. STRICT UML RELATIONSHIP SELECTION CRITERIA (MANDATORY LOGIC):\n"
    "   Select relationship types with strict object-oriented criteria. DO NOT make everything composition or inheritance:\n"
    "   - 'association' (-): DEFAULT standard structural link between independent domain entities with their own lifecycle.\n"
    "     * Use for: Docente - Curso (dicta), Estudiante - Inscripcion (se inscribe), Curso - Inscripcion, Materia - Curso, Usuario - Notificacion, Docente - Revision (evalúa).\n"
    "   - 'aggregation' (o): WEAK whole-part ('todo-parte débil'). The part CAN exist independently of the whole.\n"
    "     * Use for: Facultad o Carrera, Carrera o Materia, Departamento o Docente, Equipo o Usuario.\n"
    "   - 'composition' (*): STRONG whole-part ('todo-parte fuerte'). The child CANNOT exist without parent; cascade delete applies.\n"
    "     * Use strictly for: Curso * Tarea (las tareas pertenecen exclusivamente a ese curso), Tarea * Entrega (las entregas pertenecen a esa tarea), Entrega * Revision, Revision * Comentario.\n"
    "     * FORBIDDEN: NEVER use composition between independent master entities (NEVER Docente * Curso, NEVER Estudiante * Inscripcion, NEVER Materia * Curso).\n"
    "   - 'inheritance' (>): STRICT 'IS-A' ('es un') subtype hierarchy only.\n"
    "     * Use for: Docente > Usuario, Estudiante > Usuario, Administrador > Usuario.\n"
    "     * FORBIDDEN: NEVER use inheritance for relationships that are not genuine class specializations.\n"
    "   - 'dependency' (.): Temporary usage/service reference ('uses-a').\n"
    "   - 'realization' (~): Class implements an interface contract (Clase ~ Interfaz).\n"
    "   - Cardinalities: 1..*, 1:N, 1:1, N:M.\n"
    "5. RELATION ENDPOINTS: Identify source and target strictly by their exact CLASS NAMES (e.g., source: 'Docente', target: 'Curso').\n\n"
    "OUTPUT FORMAT: Return STRICT MINIFIED JSON ONLY:\n"
    "{\n"
    '  "summary": "Se ha consolidado y conectado el modelo universitario aplicando la semántica UML correcta (asociación, agregación, composición y generalización)...",\n'
    '  "nodes": [\n'
    '    {"name": "Usuario", "type": "class", "attributes": ["+id:int", "+nombre:string", "+email:string", "+password:string", "+rol:string"], "methods": []},\n'
    '    {"name": "Docente", "type": "class", "attributes": ["+id:int", "+especialidad:string", "+departamento:string"], "methods": []},\n'
    '    {"name": "Estudiante", "type": "class", "attributes": ["+id:int", "+matricula:string", "+carrera:string", "+#semestre:int"], "methods": []},\n'
    '    {"name": "Materia", "type": "class", "attributes": ["+id:int", "+codigo:string", "+nombre:string", "+#creditos:int"], "methods": []},\n'
    '    {"name": "Curso", "type": "class", "attributes": ["+id:int", "+#gestion:int", "+semestre:string", "+*docente_id:FK", "+*materia_id:FK"], "methods": []},\n'
    '    {"name": "Inscripcion", "type": "class", "attributes": ["+id:int", "+@fecha:date", "+estado:string", "+*estudiante_id:FK", "+*curso_id:FK"], "methods": []},\n'
    '    {"name": "Tarea", "type": "class", "attributes": ["+id:int", "+titulo:string", "+descripcion:string", "+@fechaLimite:date", "+$ponderacion:float", "+*curso_id:FK"], "methods": []},\n'
    '    {"name": "Entrega", "type": "class", "attributes": ["+id:int", "+archivo:string", "+^fechaEnvio:datetime", "+estado:string", "+*tarea_id:FK", "+*estudiante_id:FK"], "methods": []},\n'
    '    {"name": "Calificacion", "type": "class", "attributes": ["+id:int", "+$nota:float", "+observaciones:string", "+*entrega_id:FK"], "methods": []},\n'
    '    {"name": "Revision", "type": "class", "attributes": ["+id:int", "+@fecha:date", "+comentarios:string", "+$puntaje:float", "+*entrega_id:FK", "+*docente_id:FK"], "methods": []},\n'
    '    {"name": "Comentario", "type": "class", "attributes": ["+id:int", "+texto:string", "+^fecha:datetime", "+*revision_id:FK"], "methods": []},\n'
    '    {"name": "Notificacion", "type": "class", "attributes": ["+id:int", "+mensaje:string", "+^fecha:datetime", "+?leido:bool", "+*usuario_id:FK"], "methods": []}\n'
    '  ],\n'
    '  "relations": [\n'
    '    {"source": "Docente", "target": "Usuario", "type": "inheritance", "label": ""},\n'
    '    {"source": "Estudiante", "target": "Usuario", "type": "inheritance", "label": ""},\n'
    '    {"source": "Docente", "target": "Curso", "type": "association", "label": "1..*"},\n'
    '    {"source": "Materia", "target": "Curso", "type": "association", "label": "1..*"},\n'
    '    {"source": "Estudiante", "target": "Inscripcion", "type": "association", "label": "1..*"},\n'
    '    {"source": "Curso", "target": "Inscripcion", "type": "association", "label": "1..*"},\n'
    '    {"source": "Curso", "target": "Tarea", "type": "composition", "label": "1..*"},\n'
    '    {"source": "Tarea", "target": "Entrega", "type": "composition", "label": "1..*"},\n'
    '    {"source": "Estudiante", "target": "Entrega", "type": "association", "label": "1..*"},\n'
    '    {"source": "Inscripcion", "target": "Calificacion", "type": "association", "label": "1:1"},\n'
    '    {"source": "Entrega", "target": "Revision", "type": "composition", "label": "1..*"},\n'
    '    {"source": "Docente", "target": "Revision", "type": "association", "label": "1..*"},\n'
    '    {"source": "Revision", "target": "Comentario", "type": "composition", "label": "1..*"},\n'
    '    {"source": "Usuario", "target": "Notificacion", "type": "association", "label": "1..*"}\n'
    '  ],\n'
    '  "deletedNodes": ["Node_x", "Node_1", "Node_2", "Node_3", "Node_4", "Student", "Grade", "Course", "Instructor", "Assignment", "Task", "Submission", "Review", "Feedback", "Notification", "Diagrama", "eliminadas", "borradas"]\n'
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

    full_prompt = prompt
    if context:
        full_prompt = f"Contexto Actual del Diagrama:\n{context}\n\nRequerimiento:\n{prompt}"

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
    full_prompt = prompt
    if context:
        full_prompt = f"Contexto Actual:\n{context}\n\nRequerimiento:\n{prompt}"

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
        active_kimi_model = settings.KIMI_MODEL or "kimi-k3.1-pro"
        moonshot_endpoints = [
            ("https://api.moonshot.cn/v1/chat/completions", active_kimi_model),
            ("https://api.moonshot.cn/v1/chat/completions", "moonshot-v1-8k"),
            ("https://api.moonshot.cn/v1/chat/completions", "kimi-k3"),
        ]
        async with httpx.AsyncClient(timeout=60.0) as client:
            for url, model_name in moonshot_endpoints:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": UNIVERSAL_SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 8192,
                    "response_format": {"type": "json_object"}
                }
                try:
                    response = await client.post(url, json=payload, headers=moonshot_headers)
                    if response.status_code == 200:
                        data = response.json()
                        msg = data["choices"][0]["message"]
                        raw = msg.get("content") or msg.get("reasoning_content") or ""
                        cleaned = limpiar_respuesta_llm(raw)
                        if cleaned and len(cleaned) >= 15 and cleaned not in ["{", "{}", "[]", "null"]:
                            return cleaned
                    last_error = f"HTTP {response.status_code} ({model_name}): {response.text}"
                except httpx.RequestError as exc:
                    last_error = str(exc)

    # 2. Si falla o key inválida en Moonshot, consultar Kimi K3.1 Pro a través de OpenRouter
    if settings.OPENROUTE_API:
        try:
            or_headers = {
                "Authorization": f"Bearer {settings.OPENROUTE_API}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://diagramador.gerlextech.com",
                "X-Title": "Diagramador UML Colaborativo"
            }
            or_model = f"moonshotai/{settings.KIMI_MODEL or 'kimi-k3.1-pro'}"
            or_payload = {
                "model": or_model,
                "messages": [
                    {"role": "system", "content": UNIVERSAL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.2,
                "max_tokens": 8192,
                "response_format": {"type": "json_object"}
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post("https://openrouter.ai/api/v1/chat/completions", json=or_payload, headers=or_headers)
                if res.status_code == 200:
                    data = res.json()
                    msg = data["choices"][0]["message"]
                    raw = msg.get("content") or msg.get("reasoning_content") or ""
                    cleaned = limpiar_respuesta_llm(raw)
                    if cleaned and len(cleaned) >= 15 and cleaned not in ["{", "{}", "[]", "null"]:
                        return cleaned
                last_error = f"OpenRouter Kimi HTTP {res.status_code}: {res.text}"
        except Exception as or_exc:
            last_error = f"OpenRouter Kimi error: {or_exc}"

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

    full_prompt = prompt
    if context:
        full_prompt = f"Contexto Actual:\n{context}\n\nRequerimiento:\n{prompt}"

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
        "max_tokens": 4096,
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Error OpenRouter API ({response.status_code}): {response.text}")
            data = response.json()
            raw = data["choices"][0]["message"]["content"]
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

