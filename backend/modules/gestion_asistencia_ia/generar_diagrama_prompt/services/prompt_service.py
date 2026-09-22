import json
import httpx
from fastapi import HTTPException
from backend.core.config import settings

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

async def generar_diagrama_desde_prompt(prompt: str, context: str | None = None) -> dict:
    res = await _llamar_gemini(prompt, context)
    return deduplicar_resultado(res)

async def transcribe_audio_with_gemini(base64_audio: str, mime_type: str = "audio/webm") -> str:
    """Envía audio en base64 a Gemini para transcripción de voz a texto."""
    api_key = settings.GEMINI_API
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key de Gemini no configurada")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Transcribe exactamente el siguiente audio en español. Solo devuelve la transcripción de texto, sin comentarios ni explicaciones adicionales."},
                {"inlineData": {"mimeType": mime_type, "data": base64_audio}}
            ]
        }],
        "generationConfig": {
            "temperature": 0.0
        }
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post(url, json=payload)
            data = response.json()
            
            if response.status_code != 200:
                print("Gemini Audio Error:", data)
                raise HTTPException(status_code=502, detail="Error transcribiendo audio con Gemini")
                
            if "candidates" not in data or not data["candidates"]:
                raise HTTPException(status_code=500, detail="Gemini no devolvió transcripción")
                
            transcripcion = data["candidates"][0]["content"]["parts"][0]["text"]
            return transcripcion.strip()
            
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail="Error de red conectando a Gemini Audio")


async def _llamar_gemini(prompt: str, context: str | None = None) -> dict:
    api_key = settings.GEMINI_API
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key de Gemini no configurada")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "Eres un experto arquitecto de software UML y modelador de datos.\n"
        "Analiza el requerimiento del usuario y modifica o crea un diagrama UML con 'nodes' (clases/interfaces) y 'relations'.\n"
        "Se te proporciona el 'Contexto Actual' del diagrama existente.\n\n"
        "REGLAS CRÍTICAS:\n"
        "1. REGLA DE IDIOMA OBLIGATORIA: Nombra TODAS las clases, atributos y métodos en ESPAÑOL por preferencia del usuario (ejemplo: 'Estudiante', 'Grupo', 'Tarea', 'Calificacion', 'fechaEntrega: date', 'calcularPromedio(): double'). Solo usa inglés si el usuario lo especifica explícitamente.\n"
        "2. Revisa detenidamente el 'Contexto Actual' antes de crear o editar.\n"
        "3. Si vas a modificar una clase existente, REUTILIZA SU MISMO 'id' original.\n"
        "4. PROHIBIDO duplicar relaciones IDÉNTICAS (mismo tipo y misma multiplicidad/label) entre las mismas dos clases. (No crees 1:1 y 1:1 repetidos).\n"
        "5. PERMITIDO: Se pueden tener diferentes tipos o cardinalidades de relaciones entre las mismas dos clases cuando la lógica de negocio lo justifique (ejemplo: una relación 1:1 'Líder' y una relación 1:* 'Miembro' entre Estudiante y Grupo).\n"
        "6. Si se solicita conectar una clase que está suelta, conéctala de forma coherente con la clase más apropiada.\n"
        "7. Formato de 'attributes': '[visibilidad] nombre: tipo'. Usa '+' para public, '-' para private, '#' para protected (ej. '-id: int', '+nombre: string').\n"
        "8. Formato de 'methods': '[visibilidad] nombre(parametros): retorno'. Usa '+', '-', '#' (ej. '+guardar(): void').\n"
        "9. Incluye OBLIGATORIAMENTE un campo 'summary' en español que describa con claridad y precisión los cambios que realizaste en el diagrama.\n"
        "10. REGLA ESTRICTA DE IDENTIFICADOR: Toda clase debe tener un atributo identificador único (ej: 'id: int', 'id: UUID' o 'codigo: string'). Si el requerimiento no lo menciona y la clase no lo tiene, AGRÉGALO OBLIGATORIAMENTE. PERO, SI LA CLASE YA TIENE UNO (ej. 'idUsuario', 'codigo'), ¡NUNCA LO DUPLIQUES! (ej. no pongas 'id' y 'idUsuario' a la vez).\n"
        "11. HERENCIA: Para relaciones padre-hijo (herencia/generalización), DEBES usar el tipo de relación 'inheritance' (ej. {\"type\": \"inheritance\"}).\n"
        "12. TIPOS DE RELACIÓN: Los tipos válidos para 'type' en relations son: 'association', 'inheritance', 'composition', 'aggregation', 'dependency', 'realization' y 'association_class'.\n"
        "13. CLASE ASOCIACIÓN: SOLO SI el requerimiento exige explícitamente una clase intermedia (Association Class), DEBES generar tres elementos: 1) La relación principal (type: 'association') entre las clases principales. 2) Un nodo (type: 'class') para la clase intermedia. 3) Una relación (type: 'association_class') cuyo 'sourceId' sea el ID de la clase intermedia y 'targetId' sea el ID de la relación principal. ¡No la uses si es una relación normal!\n\n"
        "ESTRUCTURA DE RESPUESTA JSON:\n"
        "{\n"
        "  \"summary\": \"Resumen amigable y claro en español de las adiciones, modificaciones y relaciones creadas...\",\n"
        "  \"nodes\": [\n"
        "    { \"id\": \"id_existente_o_nuevo\", \"type\": \"class\", \"name\": \"Estudiante\", \"attributes\": [\"id: int\", \"nombre: string\"], \"methods\": [\"guardar(): void\"] }\n"
        "  ],\n"
        "  \"relations\": [\n"
        "    { \"id\": \"rel1\", \"sourceId\": \"id_fuente\", \"targetId\": \"id_destino\", \"type\": \"association\", \"label\": \"1..*\" }\n"
        "  ]\n"
        "}"
    )

    full_prompt = prompt
    if context:
        full_prompt = f"Contexto Actual del Diagrama:\n{context}\n\nRequerimiento:\n{prompt}"

    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post(url, json=payload)
            data = response.json()
            
            if response.status_code != 200:
                print(f"Gemini API Error (HTTP {response.status_code}):", data)
                raise HTTPException(status_code=502, detail=f"Error comunicándose con Gemini API: {data}")
                
            if "error" in data:
                print("Gemini API Error:", data["error"])
                raise HTTPException(status_code=502, detail=f"Error interno de la API de Google: {data['error']}")
                
            if "candidates" not in data or len(data["candidates"]) == 0:
                print("Gemini API Empty Response:", data)
                raise HTTPException(status_code=500, detail="Respuesta vacía o bloqueada por la IA")
                
            candidato = data["candidates"][0]
            
            if "finishReason" in candidato and candidato["finishReason"] != "STOP":
                print("Gemini API Security Block:", candidato["finishReason"])
                raise HTTPException(status_code=500, detail=f"Generación bloqueada por política de seguridad: {candidato['finishReason']}")
                
            texto_respuesta = candidato["content"]["parts"][0]["text"]
            
            # Limpiar posible markdown residual (```json ... ```)
            if texto_respuesta.startswith("```"):
                lines = texto_respuesta.strip().split("\n")
                if lines[0].startswith("```"): lines = lines[1:]
                if lines[-1].startswith("```"): lines = lines[:-1]
                texto_respuesta = "\n".join(lines)
                
            return json.loads(texto_respuesta)
            
        except httpx.RequestError as exc:
            print(f"HTTPX Request Error: {exc}")
            raise HTTPException(status_code=502, detail="Error de red al conectar con Gemini API")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print("Gemini API Parse Error:", e)
            raise HTTPException(status_code=500, detail=f"Formato de respuesta inválido de IA: {e}")

async def _llamar_openrouter(prompt: str, context: str | None = None) -> dict:
    api_key = settings.OPENROUTE_API
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key de OpenRouter no configurada")

    url = "https://openrouter.ai/api/v1/chat/completions"
    
    system_instruction = (
        "Eres un experto arquitecto de software UML y modelador de datos.\n"
        "Analiza el requerimiento del usuario y modifica o crea un diagrama UML con 'nodes' y 'relations'.\n"
        "Se te proporciona el 'Contexto Actual' del diagrama existente.\n\n"
        "REGLAS CRÍTICAS:\n"
        "1. REGLA DE IDIOMA OBLIGATORIA: Nombra TODAS las clases, atributos y métodos en ESPAÑOL por preferencia del usuario (ej: 'Estudiante', 'Tarea', 'nombre: string'). Solo usa inglés si se solicita explícitamente.\n"
        "2. Revisa detenidamente el 'Contexto Actual' antes de crear o editar.\n"
        "3. Si vas a modificar una clase existente, REUTILIZA SU MISMO 'id' original.\n"
        "4. PROHIBIDO duplicar relaciones IDÉNTICAS entre las mismas dos clases.\n"
        "5. Incluye OBLIGATORIAMENTE un campo 'summary' en español que describa con claridad los cambios realizados.\n\n"
        "ESTRUCTURA DE RESPUESTA JSON:\n"
        "{\n"
        "  \"summary\": \"Resumen claro en español...\",\n"
        "  \"nodes\": [\n"
        "    { \"id\": \"id_existente\", \"type\": \"class\", \"name\": \"Estudiante\", \"attributes\": [\"id: int\", \"nombre: string\"], \"methods\": [\"guardar(): void\"] }\n"
        "  ],\n"
        "  \"relations\": [\n"
        "    { \"id\": \"rel1\", \"sourceId\": \"id1\", \"targetId\": \"id2\", \"type\": \"association\", \"label\": \"1..*\" }\n"
        "  ]\n"
        "}"
    )

    full_prompt = prompt
    if context:
        full_prompt = f"Contexto Actual del Diagrama:\n{context}\n\nRequerimiento:\n{prompt}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.IA_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": full_prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                print("OpenRouter API Error:", response.text)
                raise HTTPException(status_code=502, detail="Error comunicándose con OpenRouter")
                
            data = response.json()
            texto_respuesta = data["choices"][0]["message"]["content"]
            
            texto_respuesta = texto_respuesta.strip()
            if texto_respuesta.startswith("```"):
                lines = texto_respuesta.split("\n")
                if lines[0].startswith("```"): lines = lines[1:]
                if lines[-1].startswith("```"): lines = lines[:-1]
                texto_respuesta = "\n".join(lines)
                
            return json.loads(texto_respuesta)
        except httpx.RequestError as exc:
            print(f"HTTPX Request Error: {exc}")
            raise HTTPException(status_code=502, detail="Error de red (timeout o conexión) al conectar con OpenRouter")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print("OpenRouter API Parse Error:", e)
            print("Respuesta original:", data if 'data' in locals() else 'N/A')
            raise HTTPException(status_code=500, detail="Formato de respuesta inválido de IA")
