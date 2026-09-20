import json
import httpx
from fastapi import HTTPException
from backend.core.config import settings

def deduplicar_resultado(resultado: dict) -> dict:
    """Elimina relaciones duplicadas entre el mismo par de nodos."""
    relations = resultado.get("relations", [])
    seen_relations = set()
    unique_relations = []
    
    for r in relations:
        s_id = r.get("sourceId") or r.get("origen") or r.get("source")
        t_id = r.get("targetId") or r.get("destino") or r.get("target")
        if not s_id or not t_id:
            continue
        pair_key = tuple(sorted([str(s_id), str(t_id)]))
        if pair_key not in seen_relations:
            seen_relations.add(pair_key)
            unique_relations.append(r)
            
    resultado["relations"] = unique_relations
    return resultado

async def generar_diagrama_desde_prompt(prompt: str, context: str | None = None) -> dict:
    res = await _llamar_gemini(prompt, context)
    return deduplicar_resultado(res)

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
        "1. Revisa detenidamente el 'Contexto Actual' antes de crear o editar.\n"
        "2. Si vas a modificar una clase existente, REUTILIZA SU MISMO 'id' original.\n"
        "3. PROHIBIDO duplicar relaciones entre las mismas dos clases (sourceId y targetId). Si ya están relacionadas, NO agregues otra relación duplicada.\n"
        "4. Si se solicita conectar una clase que está suelta, conéctala de forma coherente con la clase más apropiada.\n"
        "5. Formato de 'attributes': 'nombre: tipo' (sin -, +, #).\n"
        "6. Formato de 'methods': 'nombre(parametros): retorno' (sin -, +, #).\n"
        "7. Incluye OBLIGATORIAMENTE un campo 'summary' en español que describa con claridad y precisión los cambios que realizaste en el diagrama.\n\n"
        "ESTRUCTURA DE RESPUESTA JSON:\n"
        "{\n"
        "  \"summary\": \"Resumen amigable y claro en español de las adiciones, modificaciones y relaciones creadas...\",\n"
        "  \"nodes\": [\n"
        "    { \"id\": \"id_existente_o_nuevo\", \"type\": \"class\", \"name\": \"NombreClase\", \"attributes\": [\"id: int\", \"nombre: string\"], \"methods\": [\"metodo(): void\"] }\n"
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
        "1. Revisa detenidamente el 'Contexto Actual' antes de crear o editar.\n"
        "2. Si vas a modificar una clase existente, REUTILIZA SU MISMO 'id' original.\n"
        "3. PROHIBIDO duplicar relaciones entre las mismas dos clases.\n"
        "4. Incluye OBLIGATORIAMENTE un campo 'summary' en español que describa con claridad los cambios realizados.\n\n"
        "ESTRUCTURA DE RESPUESTA JSON:\n"
        "{\n"
        "  \"summary\": \"Resumen claro en español...\",\n"
        "  \"nodes\": [\n"
        "    { \"id\": \"id_existente\", \"type\": \"class\", \"name\": \"ClaseA\", \"attributes\": [\"id: int\"], \"methods\": [\"metodo(): void\"] }\n"
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
