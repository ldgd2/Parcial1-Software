import json
import httpx
from fastapi import HTTPException
from backend.core.config import settings

async def digitalizar_diagrama_desde_imagen(image_base64: str, prompt: str | None = None) -> dict:
    return await _llamar_gemini_vision(image_base64, prompt)

async def _llamar_gemini_vision(image_base64: str, prompt: str | None = None) -> dict:
    api_key = settings.IMAGE_OPEROUTE_API or settings.GEMINI_API
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key de Gemini no configurada")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "Eres un experto arquitecto de software UML. El usuario te dará una imagen de un diagrama UML. "
        "Debes extraer las clases, sus atributos, métodos y sus relaciones. "
        "REGLA DE IDIOMA: De preferencia nombra o traduce las clases, atributos y métodos al ESPAÑOL (ejemplo: 'Estudiante', 'nombre: string', 'calcularPromedio(): double') a menos que el texto en la imagen esté explícitamente escrito en otro idioma.\n"
        "IMPORTANTE: En los elementos de 'attributes' y 'methods', DEBES incluir los símbolos de visibilidad (+ para public, - para private, # para protected) al inicio del string.\n"
        "Formato exacto de atributo: '[visibilidad] nombre: tipo' (ejemplo: '-id: int', '+nombre: string').\n"
        "Formato exacto de método: '[visibilidad] nombre(parametros): retorno' (ejemplo: '+guardar(): void', '-obtenerPorId(id: int): Estudiante').\n"
        "REGLA ESTRICTA DE IDENTIFICADOR: Toda clase debe tener un atributo identificador (ej: 'id: int' o 'codigo: string'). Si la imagen no lo tiene, AGRÉGALO OBLIGATORIAMENTE. PERO, SI YA TIENE UNO (ej. 'idUsuario', 'codigo'), ¡NUNCA LO DUPLIQUES!.\n"
        "HERENCIA: Si detectas herencia en la imagen (flechas con punta triangular vacía apuntando al padre), usa el tipo de relación 'generalization' (ej. {\"type\": \"generalization\"}) en vez de 'association'.\n"
        "Devuelve SOLO un JSON válido con esta estructura (sin markdown ni explicaciones):\n"
        "{\n"
        "  \"nodes\": [\n"
        "    { \"id\": \"ClaseA\", \"type\": \"class\", \"name\": \"Estudiante\", \"attributes\": [\"id: int\", \"nombre: string\"], \"methods\": [\"guardar(): void\"] }\n"
        "  ],\n"
        "  \"relations\": [\n"
        "    { \"id\": \"rel1\", \"sourceId\": \"ClaseA\", \"targetId\": \"ClaseB\", \"type\": \"association\", \"label\": \"1..*\" }\n"
        "  ]\n"
        "}"
    )

    # Limpiar el base64 si tiene el prefijo de data URI
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]

    text_prompt = "Digitaliza este diagrama UML."
    if prompt:
        text_prompt += f" Considera además el siguiente comentario o requerimiento del usuario: {prompt}"

    payload = {
        "contents": [{
            "parts": [
                {"text": text_prompt},
                {"inlineData": {"mimeType": "image/jpeg", "data": image_base64}}
            ]
        }],
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
                print(f"Gemini Vision API Error (HTTP {response.status_code}):", data)
                raise HTTPException(status_code=502, detail=f"Error comunicándose con Gemini API: {data}")
                
            if "error" in data:
                print("Gemini Vision API Error:", data["error"])
                raise HTTPException(status_code=502, detail=f"Error interno de la API de Google: {data['error']}")
                
            if "candidates" not in data or len(data["candidates"]) == 0:
                print("Gemini Vision API Empty Response:", data)
                raise HTTPException(status_code=500, detail="Respuesta vacía o bloqueada por la IA")
                
            candidato = data["candidates"][0]
            
            if "finishReason" in candidato and candidato["finishReason"] != "STOP":
                print("Gemini Vision API Security Block:", candidato["finishReason"])
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
            print("Gemini Vision API Parse Error:", e)
            raise HTTPException(status_code=500, detail=f"Formato de respuesta inválido de IA: {e}")


async def _llamar_openrouter_vision(image_base64: str, context: str | None = None) -> dict:
    api_key = settings.IMAGE_OPEROUTE_API or settings.OPENROUTE_API
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key de OpenRouter no configurada")

    url = "https://openrouter.ai/api/v1/chat/completions"
    
    system_instruction = (
        "Eres un experto arquitecto de software UML. Extrae las clases y relaciones de la imagen. "
        "IMPORTANTE: En los elementos de 'attributes' y 'methods', NO incluyas los símbolos de visibilidad (-, +, #) dentro del string.\n"
        "Formato exacto de atributo: 'nombre: tipo' (ejemplo: 'id: int', 'username: string').\n"
        "Formato exacto de método: 'nombre(parametros): retorno' (ejemplo: 'save(): void', 'findById(id: int): User').\n"
        "Devuelve SOLO JSON:\n"
        "{\n"
        "  \"nodes\": [\n"
        "    { \"id\": \"uuid1\", \"type\": \"class\", \"name\": \"ClaseA\", \"attributes\": [\"id: int\", \"name: string\"], \"methods\": [\"save(): void\"] }\n"
        "  ],\n"
        "  \"relations\": [\n"
        "    { \"id\": \"rel1\", \"sourceId\": \"uuid1\", \"targetId\": \"uuid2\", \"type\": \"association\", \"label\": \"1..*\" }\n"
        "  ]\n"
        "}"
    )

    if not image_base64.startswith("data:image"):
        image_base64 = f"data:image/jpeg;base64,{image_base64}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.IA_MODEL, # Usar el modelo del config en vez de hardcodear google/gemini-pro-vision
        "messages": [
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Digitaliza este diagrama UML."},
                    {"type": "image_url", "image_url": {"url": image_base64}}
                ]
            }
        ],
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print("OpenRouter Vision Error:", response.text)
            raise HTTPException(status_code=502, detail="Error comunicándose con OpenRouter Vision")
            
        data = response.json()
        try:
            texto_respuesta = data["choices"][0]["message"]["content"]
            return json.loads(texto_respuesta)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print("OpenRouter Vision Parse Error:", e)
            raise HTTPException(status_code=500, detail="Formato de respuesta inválido de IA")
