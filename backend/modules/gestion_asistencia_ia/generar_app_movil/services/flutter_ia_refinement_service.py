import re
import httpx
from typing import Tuple

from backend.core.config import settings


def _clean_dart_code(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


# Paquetes que existen en el pubspec generado: cualquier otro import es una alucinación
PAQUETES_PERMITIDOS = ("flutter", "http", "intl", "flutter_dotenv")


def validar_codigo_refinado(original: str, refinado: str) -> str:
    """'' si el código refinado es aceptable; si no, el motivo para descartarlo."""
    if not refinado or len(refinado) < 50:
        return "respuesta vacía"
    for paquete in re.findall(r"import\s+'package:([a-zA-Z0-9_]+)/", refinado):
        if paquete not in PAQUETES_PERMITIDOS:
            return f"usa el paquete '{paquete}', que no está en el proyecto"
    faltan = set(re.findall(r"\bclass\s+(\w+)", original)) - set(re.findall(r"\bclass\s+(\w+)", refinado))
    if faltan:
        return f"eliminó o renombró las clases {', '.join(sorted(faltan))}"
    if refinado.count("{") != refinado.count("}") or refinado.count("(") != refinado.count(")"):
        return "llaves o paréntesis desbalanceados (código cortado)"
    return ""


def _aceptar(original: str, refinado: str, vista: str, proveedor: str):
    motivo = validar_codigo_refinado(original, refinado)
    if motivo:
        return None, f"Se descartó la propuesta de {proveedor} para {vista}: {motivo}."
    return refinado, f"Refinamiento de {vista} aplicado con {proveedor}."


async def refinar_codigo_con_ia(
    vista_nombre: str,
    codigo_actual: str,
    instrucciones: str,
    api_endpoint: str = ""
) -> Tuple[str, str]:
    """
    Refinamiento quirúrgico con IA ultra-optimizado en consumo de tokens.
    Solo envía el fragmento necesario y solicita transformaciones concretas
    sin re-generar archivos gigantescos desde cero.
    """
    provider = (settings.AI_PROVIDER or "kimi").lower().strip()
    descartes = []

    prompt_minificado = (
        f"Target: Flutter Widget '{vista_nombre}'\n"
        f"API Endpoint: '{api_endpoint}'\n"
        f"Requirement: {instrucciones}\n"
        f"Input Dart Code:\n{codigo_actual}\n\n"
        f"Rules: Output ONLY the full updated Dart file. No markdown fences. No explanations. "
        f"Keep every existing class name, import path and the API endpoint. "
        f"Only these packages exist: {', '.join(PAQUETES_PERMITIDOS)}. Do not invent fields, routes or packages."
    )

    system_instruction = (
        "Role: Senior Flutter & Dart Architect. "
        "Refine code with robust error handling and Material 3 UI. Return pure Dart code."
    )

    # 1. Kimi Moonshot
    if provider == "kimi" or settings.KIMI_API:
        key = settings.KIMI_API
        if key:
            model = settings.KIMI_MODEL or "kimi-k3.1-pro"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt_minificado}
                ],
                "temperature": 0.1,
                "max_tokens": 8000,
            }
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    res = await client.post(
                        "https://api.moonshot.ai/v1/chat/completions",
                        json=payload,
                        headers={"Authorization": f"Bearer {key}"}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        raw_content = data["choices"][0]["message"]["content"]
                        refined = _clean_dart_code(raw_content)
                        codigo, aviso = _aceptar(codigo_actual, refined, vista_nombre, "Kimi")
                        if codigo:
                            return codigo, aviso
                        descartes.append(aviso)
            except Exception:
                pass

    # 2. Gemini fallback
    if settings.GEMINI_API:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_instruction}\n\n{prompt_minificado}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8000
            }
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    parts = data.get("candidates", [])[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        refined = _clean_dart_code(parts[0]["text"])
                        codigo, aviso = _aceptar(codigo_actual, refined, vista_nombre, "Gemini")
                        if codigo:
                            return codigo, aviso
                        descartes.append(aviso)
        except Exception:
            pass

    if descartes:
        return codigo_actual, " ".join(descartes) + " Se mantuvo el código original."
    return codigo_actual, f"Se mantuvo el código original para {vista_nombre} (IA no disponible)."

