import os
import re
import asyncio
import httpx
from backend.core.config import settings

async def inyectar_logica_ia(temp_dir: str):
    """
    Escanea la carpeta de código generado buscando marcadores de IA,
    extrae el prompt, consulta a OpenRouter/Gemini en paralelo, y 
    reemplaza los bloques con código real.
    """
    java_files = []
    for root, _, files in os.walk(os.path.join(temp_dir, "src", "main", "java")):
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.join(root, file))

    regex = re.compile(r"// @IA_PROMPT_START:\s*\"([^\"]+)\"\s*// @IA_PROMPT_END", re.DOTALL)
    
    # Recolectar todas las tareas (archivo, coincidencia, prompt)
    tareas = []
    
    for filepath in java_files:
        with open(filepath, "r", encoding="utf-8") as f:
            contenido = f.read()
            
        for match in regex.finditer(contenido):
            prompt = match.group(1)
            token_a_reemplazar = match.group(0)
            tareas.append({
                "filepath": filepath,
                "token": token_a_reemplazar,
                "prompt": prompt
            })

    if not tareas:
        return # Nada que inyectar
        
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Ejecutar peticiones en paralelo
        resultados = await asyncio.gather(*(
            pedir_codigo_ia(t["prompt"], client) for t in tareas
        ), return_exceptions=True)
        
    # Agrupar reemplazos por archivo para no machacar lecturas concurrentes del FS
    reemplazos_por_archivo = {}
    for i, tarea in enumerate(tareas):
        resultado = resultados[i]
        if isinstance(resultado, Exception) or not resultado:
            codigo = f"// Error de la IA al generar código: {str(resultado)}"
        else:
            codigo = resultado
            
        fp = tarea["filepath"]
        if fp not in reemplazos_por_archivo:
            reemplazos_por_archivo[fp] = []
        reemplazos_por_archivo[fp].append((tarea["token"], codigo))
        
    # Aplicar los cambios físicamente
    for filepath, reemplazos in reemplazos_por_archivo.items():
        with open(filepath, "r", encoding="utf-8") as f:
            contenido = f.read()
            
        for token, nuevo_codigo in reemplazos:
            contenido = contenido.replace(token, nuevo_codigo)
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(contenido)

async def pedir_codigo_ia(prompt: str, client: httpx.AsyncClient) -> str:
    system_prompt = (
        "Eres un experto arquitecto de Spring Boot y Java 17. "
        "Escribe el interior del método basándote en la solicitud del usuario. "
        "Devuelve SOLO el código Java válido (sin firmas de método extra, sin markdown, sin explicaciones). "
        "Solo la lógica interna que va entre las llaves { } del método."
    )
    
    headers = {
        "Authorization": f"Bearer {settings.IA_API}",
        "Content-Type": "application/json"
    }
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    response = await client.post(url, json={
        "model": settings.IA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }, headers=headers)
    
    if response.status_code == 200:
        texto = response.json()['choices'][0]['message']['content'].strip()
        texto = texto.replace("```java", "").replace("```", "")
        return texto
    else:
        return f"// Error HTTP {response.status_code}: {response.text}"
