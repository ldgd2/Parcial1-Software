import os
import re
import shutil
import subprocess
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

# Firma del método justo antes del marcador (la escribe templates/Service.java.jinja)
_FIRMA = re.compile(r"public\s+([\w<>\[\], ?]+?)\s+(\w+)\s*\(([^)]*)\)\s*\{\s*$")
_ERROR_JAVA = re.compile(r"\[ERROR\]\s+(.+?\.java):\[(\d+),\d+\]")


def cuerpo_por_defecto(metodo: str, motivo: str = "") -> str:
    """Cuerpo que SIEMPRE compila, sea cual sea el tipo de retorno."""
    nota = f"\n// {motivo}" if motivo else ""
    return (f"// TODO: implementar {metodo}{nota}\n"
            f"throw new UnsupportedOperationException(\"{metodo} aún no está implementado\");")


def _bloque(n: int, codigo: str) -> str:
    return f"// @IA_BEGIN {n}\n{codigo}\n// @IA_END {n}"


def _contexto_metodo(contenido: str, inicio: int, archivo: str) -> dict:
    lineas_previas = contenido[:inicio].rstrip().splitlines()
    firma = _FIRMA.search(lineas_previas[-1]) if lineas_previas else None
    clase_service = os.path.splitext(os.path.basename(archivo))[0]
    return {
        "retorno": firma.group(1).strip() if firma else "void",
        "nombre": firma.group(2) if firma else "metodo",
        "parametros": firma.group(3).strip() if firma else "",
        "service": clase_service,
        "entidad": clase_service[:-len("Service")] if clase_service.endswith("Service") else clase_service,
    }


async def inyectar_logica_ia(temp_dir: str, diagram_json: dict = None, descripcion_proyecto: str = ""):
    """
    Escanea la carpeta de código generado buscando marcadores de IA,
    extrae el prompt, consulta a OpenRouter/Gemini en paralelo con contexto del diagrama,
    y reemplaza los bloques con código Java funcional.

    Luego COMPILA el backend (si hay Maven) y todo método escrito por la IA que no compile se
    cambia por un cuerpo por defecto: antes un `atributo` inventado por la IA rompía la
    compilación y el auto-despliegue entero fallaba.
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
            tareas.append({
                "filepath": filepath,
                "token": match.group(0),
                "prompt": match.group(1),
                "metodo": _contexto_metodo(contenido, match.start(), filepath),
            })

    if not tareas:
        return

    async with httpx.AsyncClient(timeout=60.0) as client:
        resultados = await asyncio.gather(*(
            pedir_codigo_ia(t["prompt"], contexto_str, client, t["metodo"]) for t in tareas
        ), return_exceptions=True)

    reemplazos_por_archivo = {}
    for n, (tarea, resultado) in enumerate(zip(tareas, resultados)):
        nombre = tarea["metodo"]["nombre"]
        if isinstance(resultado, Exception) or not resultado or str(resultado).startswith("// Error"):
            motivo = str(resultado).splitlines()[0][:150] if resultado else "la IA no respondió"
            codigo = cuerpo_por_defecto(nombre, f"La IA no pudo generarlo: {motivo}")
        else:
            codigo = resultado
        reemplazos_por_archivo.setdefault(tarea["filepath"], []).append((tarea["token"], _bloque(n, codigo)))

    for filepath, reemplazos in reemplazos_por_archivo.items():
        with open(filepath, "r", encoding="utf-8") as f:
            contenido = f.read()
        for token, nuevo_codigo in reemplazos:
            contenido = contenido.replace(token, nuevo_codigo, 1)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(contenido)

    await asyncio.to_thread(asegurar_que_compila, temp_dir)


def _compilar(proyecto_dir: str):
    """(salida, código) de `mvn compile`; None si no hay Maven o no termina a tiempo."""
    mvn = shutil.which("mvn")
    if not mvn:
        return None
    try:
        r = subprocess.run([mvn, "-B", "-q", "compile"], cwd=proyecto_dir,
                           capture_output=True, text=True, timeout=300)
        return r.stdout + r.stderr, r.returncode
    except Exception as e:
        print(f"[IA] No se pudo verificar la compilación: {e}")
        return None


def asegurar_que_compila(proyecto_dir: str, intentos: int = 3) -> bool:
    """Compila; cada bloque @IA_BEGIN..@IA_END con errores pasa a un cuerpo por defecto."""
    if not os.path.isfile(os.path.join(proyecto_dir, "pom.xml")):
        return False
    for _ in range(intentos):
        res = _compilar(proyecto_dir)
        if res is None:
            print("[IA] Maven no disponible: no se verificó la compilación del código de la IA.")
            return False
        salida, codigo = res
        if codigo == 0:
            return True
        errores = {}
        for ruta, linea in _ERROR_JAVA.findall(salida):
            ruta = ruta.strip()
            if re.match(r"^/[A-Za-z]:/", ruta):  # Maven en Windows: /C:/...
                ruta = ruta[1:]
            errores.setdefault(os.path.normcase(os.path.abspath(ruta)), set()).add(int(linea))
        if not errores:
            print("[IA] La compilación falló sin errores de código (dependencias/JDK): " + salida.strip()[-300:])
            return False
        corregidos = sum(_reemplazar_bloques_con_error(ruta, lineas) for ruta, lineas in errores.items())
        if not corregidos:
            print("[IA] Errores de compilación fuera del código de la IA:\n" + "\n".join(
                l for l in salida.splitlines() if "[ERROR]" in l)[:1500])
            return False
        print(f"[IA] {corregidos} método(s) generados por la IA no compilaban: se dejaron como TODO.")
    return False


def _reemplazar_bloques_con_error(ruta: str, lineas_error: set) -> int:
    """Cambia por el cuerpo por defecto cada bloque de la IA que contenga una línea con error."""
    if not os.path.isfile(ruta):
        return 0
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = f.read().split("\n")
    bloques, abierto = [], None
    for i, l in enumerate(lineas, start=1):
        m = re.match(r"\s*// @IA_(BEGIN|END) (\d+)\s*$", l)
        if m and m.group(1) == "BEGIN":
            abierto = (int(m.group(2)), i)
        elif m and abierto and int(m.group(2)) == abierto[0]:
            bloques.append((abierto[0], abierto[1], i))
            abierto = None
    malos = [(n, a, b) for n, a, b in bloques if any(a <= e <= b for e in lineas_error)]
    for n, a, b in sorted(malos, key=lambda x: x[1], reverse=True):
        previa = "\n".join(lineas[:a - 1])
        nombre = _contexto_metodo(previa, len(previa), ruta)["nombre"]
        lineas[a - 1:b] = _bloque(n, cuerpo_por_defecto(
            nombre, "El código generado por la IA no compilaba")).split("\n")
    if malos:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))
    return len(malos)


async def pedir_codigo_ia(prompt: str, contexto_str: str, client: httpx.AsyncClient, metodo: dict = None) -> str:
    metodo = metodo or {}
    entidad = metodo.get("entidad", "Entidad")
    service = metodo.get("service", f"{entidad}Service")
    system_prompt = (
        "Eres un experto arquitecto de backend en Spring Boot 3 y Java 17.\n"
        "Tu tarea es escribir el cuerpo ejecutable Java de un método de servicio basándote en la solicitud del usuario.\n\n"
        f"{contexto_str}\n\n"
        f"DÓNDE ESTÁ EL MÉTODO: dentro de la clase `com.proyecto.services.{service}` (NO dentro de la entidad).\n"
        f"Firma exacta: public {metodo.get('retorno', 'void')} {metodo.get('nombre', 'metodo')}({metodo.get('parametros', '')})\n"
        f"Campos disponibles en {service}: SOLO `repository` ({entidad}Repository: findAll(), findById(UUID), save(), deleteById(UUID), count()).\n"
        "Variables disponibles: SOLO los parámetros de la firma y las que declares tú.\n\n"
        "REGLAS CRÍTICAS DE COMPILACIÓN:\n"
        "1. Devuelve ÚNICAMENTE el código Java ejecutable que va dentro de las llaves { } del método.\n"
        "2. NO incluyas bloques markdown (sin ```java), ni explicaciones ni firmas del método.\n"
        f"3. Los atributos de la entidad NO son variables aquí: obtén entidades con `repository` y usa sus getters/setters "
        f"(p. ej. `repository.findAll().stream().mapToInt({entidad}::getX)...`). Nunca uses un atributo suelto.\n"
        "4. Usa nombres totalmente calificados para lo que no sea java.lang (java.util.List, java.util.stream.Collectors...).\n"
        "5. El código DEBE compilar. Si el método no es void, todas las ramas deben retornar un valor del tipo exacto.\n"
        "6. Si no puedes implementarlo con certeza, devuelve: throw new UnsupportedOperationException(\"pendiente\");"
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
