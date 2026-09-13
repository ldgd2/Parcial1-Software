import json
import httpx
from fastapi import HTTPException
from backend.core.config import settings

async def generar_diagrama_desde_prompt(prompt: str) -> dict:
    if settings.IA_SERVICE == "googlecloud":
        return await _llamar_gemini(prompt)
    elif settings.IA_SERVICE == "openroute":
        return await _llamar_openrouter(prompt)
    else:
        raise HTTPException(status_code=500, detail="Servicio de IA no configurado correctamente")

async def _llamar_gemini(prompt: str) -> dict:
    api_key = settings.IA_API
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key de Gemini no configurada")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "Eres un experto arquitecto de software UML. El usuario te dará una descripción de un sistema, "
        "y debes generar un diagrama de clases UML representándolo. Devuelve SOLO un JSON válido con esta estructura exacta "
        "(sin markdown ni explicaciones):\n"
        "{\n"
        "  \"nodes\": [\n"
        "    { \"id\": \"ClaseA\", \"type\": \"class\", \"name\": \"ClaseA\", \"attributes\": [\"- id: int\"], \"methods\": [\"+ save()\"] }\n"
        "  ],\n"
        "  \"relations\": [\n"
        "    { \"id\": \"rel1\", \"sourceId\": \"ClaseA\", \"targetId\": \"ClaseB\", \"type\": \"association\", \"label\": \"1..*\" }\n"
        "  ]\n"
        "}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
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

async def _llamar_openrouter(prompt: str) -> dict:
    api_key = settings.IA_API
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key de OpenRouter no configurada")

    url = "https://openrouter.ai/api/v1/chat/completions"
    
    system_instruction = (
        "Eres un experto arquitecto de software UML. Genera un diagrama de clases en JSON válido. Devuelve SOLO el JSON:\n"
        "{\n"
        "  \"nodes\": [\n"
        "    { \"id\": \"uuid1\", \"type\": \"class\", \"name\": \"ClaseA\", \"attributes\": [\"- id: int\"], \"methods\": [\"+ save()\"] }\n"
        "  ],\n"
        "  \"relations\": [\n"
        "    { \"id\": \"rel1\", \"sourceId\": \"uuid1\", \"targetId\": \"uuid2\", \"type\": \"association\", \"label\": \"1..*\" }\n"
        "  ]\n"
        "}"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-pro", # modelo por defecto para openrouter
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print("OpenRouter API Error:", response.text)
            raise HTTPException(status_code=502, detail="Error comunicándose con OpenRouter")
            
        data = response.json()
        try:
            texto_respuesta = data["choices"][0]["message"]["content"]
            return json.loads(texto_respuesta)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print("OpenRouter API Parse Error:", e)
            raise HTTPException(status_code=500, detail="Formato de respuesta inválido de IA")
