import httpx
from backend.core.config import settings

async def generar_mensaje_commit_ia(diff_content: str) -> str:
    """
    Envía el diff de git a la IA para que genere un mensaje de commit estructurado.
    """
    if not diff_content or len(diff_content.strip()) == 0:
        return "Actualizacion automatica de codigo"

    system_prompt = (
        "Eres un experto ingeniero de software y mantenedor de repositorios. "
        "Tu tarea es leer el siguiente git diff y generar un único mensaje de commit claro y conciso. "
        "El mensaje debe seguir la convención de 'Conventional Commits' (feat:, fix:, chore:, refactor:, etc.). "
        "NO incluyas explicaciones, saludos ni markdown de bloque de código, SOLO el mensaje del commit en texto plano.\n"
        "ESTA ESTRICTAMENTE PROHIBIDO EL USO DE EMOJIS.\n"
        "Si el diff es muy grande, resume los cambios principales."
    )
    
    headers = {
        "Authorization": f"Bearer {settings.IA_API}",
        "Content-Type": "application/json"
    }
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    try:
        # Limitar el tamaño del diff para no exceder tokens (aprox 10,000 caracteres)
        diff_truncado = diff_content[:10000]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={
                "model": settings.IA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Git Diff:\n{diff_truncado}"}
                ]
            }, headers=headers)
            
        if response.status_code == 200:
            texto = response.json()['choices'][0]['message']['content'].strip()
            # Limpiar posible markdown
            texto = texto.replace("```", "").strip()
            return texto
        else:
            return "Actualizacion de codigo (Generado por IA fallback)"
    except Exception as e:
        return f"Actualizacion de codigo (IA error: {str(e)[:50]})"
