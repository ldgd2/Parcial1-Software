import os
import re
import asyncio
import httpx
from backend.core.config import settings

def construir_contexto_diagrama(diagram_json: dict = None, descripcion_proyecto: str = "") -> str:
    if not diagram_json:
        diagram_json = {}
        
    ctx = []
    if descripcion_proyecto:
        ctx.append(f"DESCRIPCIÓN Y PROPÓSITO DEL PROYECTO:\n{descripcion_proyecto}\n")
        
    nodos = diagram_json.get("nodes", [])
    relaciones = diagram_json.get("edges", []) or diagram_json.get("relations", [])
    
    id_to_name = {}
    ctx.append("MODELO DE DATOS Y ENTIDADES (SPRING BOOT JPA):")
    for n in nodos:
        if n.get("type") in ["class", "interface"]:
            nombre = n.get("nombre", "Entidad")
            id_to_name[n.get("id")] = nombre
            attrs = [f"{a.get('nombre')}: {a.get('tipo', 'String')}" for a in n.get("atributos", [])]
            metodos = [f"{m.get('nombre')}({m.get('parametros', '')}): {m.get('retorno', 'void')}" for m in n.get("metodos", [])]
            ctx.append(f"- Entidad `{nombre}`:")
            ctx.append(f"  Atributos: {', '.join(attrs) if attrs else 'id (UUID), createdAt, updatedAt, isActive'}")
            if metodos:
                ctx.append(f"  Métodos: {', '.join(metodos)}")

    if relaciones:
        ctx.append("\nRELACIONES ENTRE ENTIDADES:")
        for r in relaciones:
            orig = id_to_name.get(r.get("origen") or r.get("source"), r.get("origen"))
            dest = id_to_name.get(r.get("destino") or r.get("target"), r.get("destino"))
            tipo = r.get("tipo", "relacion")
            mult_o = r.get("multiplicidadOrigen", r.get("sourceMultiplicity", ""))
            mult_d = r.get("multiplicidadDestino", r.get("targetMultiplicity", ""))
            ctx.append(f"- {orig} ({mult_o}) --[{tipo}]--> {dest} ({mult_d})")

    return "\n".join(ctx)

async def inyectar_logica_ia(temp_dir: str, diagram_json: dict = None, descripcion_proyecto: str = ""):
    """
    Escanea la carpeta de código generado buscando marcadores de IA,
    extrae el prompt, consulta a OpenRouter/Gemini en paralelo con contexto del diagrama,
    y reemplaza los bloques con código Java funcional.
    """
    contexto_str = construir_contexto_diagrama(diagram_json, descripcion_proyecto)
    
    java_files = []
    for root, _, files in os.walk(os.path.join(temp_dir, "src", "main", "java")):
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.join(root, file))

    regex = re.compile(r"// @IA_PROMPT_START:\s*\"([^\"]+)\"\s*// @IA_PROMPT_END", re.DOTALL)
    
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
        return
        
    async with httpx.AsyncClient(timeout=60.0) as client:
        resultados = await asyncio.gather(*(
            pedir_codigo_ia(t["prompt"], contexto_str, client) for t in tareas
        ), return_exceptions=True)
        
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
        
    for filepath, reemplazos in reemplazos_por_archivo.items():
        with open(filepath, "r", encoding="utf-8") as f:
            contenido = f.read()
            
        for token, nuevo_codigo in reemplazos:
            contenido = contenido.replace(token, nuevo_codigo)
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(contenido)

async def pedir_codigo_ia(prompt: str, contexto_str: str, client: httpx.AsyncClient) -> str:
    system_prompt = (
        "Eres un experto arquitecto de backend en Spring Boot 3 y Java 17.\n"
        "Tu tarea es escribir el cuerpo ejecutable Java de un método de servicio basándote en la solicitud del usuario.\n\n"
        f"{contexto_str}\n\n"
        "REGLAS CRÍTICAS DE COMPILACIÓN:\n"
        "1. Devuelve ÚNICAMENTE el código Java ejecutable que va dentro de las llaves { } del método.\n"
        "2. NO incluyas bloques markdown (sin ```java), ni explicaciones ni firmas del método.\n"
        "3. Tienes acceso al campo `repository` (Spring Data JPA Repository con findAll(), findById(), save(), deleteById(), etc.).\n"
        "4. El código DEBE compilar perfectamente. Usa Java Streams, lambdas u operaciones coherentes con el modelo de datos expuesto.\n"
        "5. Si el método retorna un objeto o DTO, construye la instancia o retorna el resultado mapeado correspondiente."
    )
    
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTE_API}",
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
        texto = texto.replace("```java", "").replace("```", "").strip()
        return texto
    else:
        return f"// Error HTTP {response.status_code}: {response.text}"
