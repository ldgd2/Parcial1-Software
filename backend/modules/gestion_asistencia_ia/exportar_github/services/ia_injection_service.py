import os
import re
import shutil
import subprocess
import asyncio
import httpx
from backend.core.config import settings
from backend.modules.gestion_asistencia_ia.generar_diagrama_prompt.services.llm_client import (
    _registrar_uso,
    hay_presupuesto,
)

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
_FIRMA = re.compile(r"public\s+([\w<>\[\], ?.]+?)\s+(\w+)\s*\(([^)]*)\)\s*\{\s*$")
_ERROR_JAVA = re.compile(r"\[ERROR\]\s+(.+?\.java):\[(\d+),\d+\]\s*(.*)")
_CAMPO_JAVA = re.compile(r"^\s*private\s+([\w.<>, ?\[\]]+?)\s+(\w+)\s*(?:=[^;]*)?;", re.M)
_MAX_PARALELO = 4


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


# ── lo que la IA puede usar (leído del código generado, no inventado) ─────────

def _leer_java(raiz_java: str, *partes: str) -> str:
    ruta = os.path.join(raiz_java, "com", "proyecto", *partes)
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _accesores(fuente: str) -> list:
    """['String getNombre()', 'void setNombre(String)', ...] de los campos de una clase Lombok @Data."""
    res = []
    for tipo, nombre in _CAMPO_JAVA.findall(fuente):
        cap = nombre[0].upper() + nombre[1:]
        res.append(f"{tipo} get{cap}()")
        res.append(f"void set{cap}({tipo} valor)")
    return res


def contexto_entidad(temp_dir: str, entidad: str) -> str:
    """Código real de la entidad + getters/setters exactos (Lombok) para que la IA no invente nombres."""
    raiz = os.path.join(temp_dir, "src", "main", "java")
    entidad_src = _leer_java(raiz, "models", f"{entidad}.java")
    base_src = _leer_java(raiz, "common", "BaseEntity.java")
    accesores = _accesores(entidad_src) + _accesores(base_src)
    partes = []
    if entidad_src:
        partes.append(f"Código de la entidad com.proyecto.models.{entidad} (Lombok @Data genera getters/setters):\n"
                      f"```java\n{entidad_src.strip()}\n```")
    if accesores:
        partes.append(f"Métodos EXACTOS disponibles en {entidad} (no existen otros):\n- " + "\n- ".join(accesores))
    partes.append(f"Repositorio: `repository` es {entidad}Repository extends JpaRepository<{entidad}, java.util.UUID>: "
                  "findAll(), findById(UUID) -> Optional, save(e), saveAll(lista), deleteById(UUID), existsById(UUID), count().")
    return "\n\n".join(partes)


# ── cliente de IA para código: Kimi primero, con respaldo ─────────────────────

def _orden_proveedores() -> list:
    disponibles = {
        "kimi": bool(settings.KIMI_API),
        "openrouter": bool(settings.OPENROUTE_API),
        "gemini": bool(settings.GEMINI_API),
    }
    orden = ["kimi", "openrouter", "gemini"]
    preferido = (settings.AI_PROVIDER or "").lower()
    if preferido in orden and preferido != "kimi" and not disponibles["kimi"]:
        orden.remove(preferido)
        orden.insert(0, preferido)
    return [p for p in orden if disponibles[p]]


async def _llamar(client: httpx.AsyncClient, proveedor: str, system: str, user: str) -> str:
    if proveedor == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API}"
        r = await client.post(url, json={
            "contents": [{"parts": [{"text": user}]}],
            "systemInstruction": {"parts": [{"text": system}]},
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192},
        })
        if r.status_code != 200:
            raise RuntimeError(f"gemini HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        um = data.get("usageMetadata") or {}
        _registrar_uso("gemini:codigo", um.get("promptTokenCount"),
                       (um.get("candidatesTokenCount") or 0) + (um.get("thoughtsTokenCount") or 0), system + user, r.text)
        return data["candidates"][0]["content"]["parts"][0]["text"]

    if proveedor == "kimi":
        url, key = "https://api.moonshot.ai/v1/chat/completions", settings.KIMI_API
        modelo = settings.KIMI_MODEL or "kimi-k3"
        temperatura = 1.0 if ("k3" in modelo.lower() or "kimi" in modelo.lower()) else 0.2
    else:
        url, key = "https://openrouter.ai/api/v1/chat/completions", settings.OPENROUTE_API
        modelo, temperatura = settings.IA_MODEL, 0.1
    r = await client.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={
        "model": modelo,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperatura,
        "max_tokens": 8192,
    })
    if r.status_code != 200:
        raise RuntimeError(f"{proveedor} HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    u = data.get("usage") or {}
    _registrar_uso(f"{proveedor}:{modelo}:codigo", u.get("prompt_tokens"), u.get("completion_tokens"), system + user, r.text)
    msg = data["choices"][0]["message"]
    return msg.get("content") or msg.get("reasoning_content") or ""


async def llm_codigo(client: httpx.AsyncClient, system: str, user: str) -> str:
    """Pide código a Kimi (o al siguiente proveedor con llave si falla). Devuelve texto crudo."""
    errores = []
    for proveedor in _orden_proveedores():
        if not hay_presupuesto():
            errores.append("sin presupuesto de IA")
            break
        try:
            texto = await _llamar(client, proveedor, system, user)
            if texto and texto.strip():
                return texto
            errores.append(f"{proveedor}: respuesta vacía")
        except Exception as e:  # red, cuota, formato…
            errores.append(f"{proveedor}: {str(e)[:160]}")
    raise RuntimeError("; ".join(errores) or "no hay proveedores de IA configurados")


def extraer_cuerpo(texto: str, nombre_metodo: str = "") -> str:
    """Solo el cuerpo del método: sin <think>, sin ``` y sin la firma si la IA la repitió."""
    texto = re.sub(r"<think>.*?</think>", "", texto or "", flags=re.S).strip()
    bloques = re.findall(r"```(?:java)?\s*\n(.*?)```", texto, flags=re.S)
    if bloques:
        texto = max(bloques, key=len)
    texto = texto.replace("```java", "").replace("```", "").strip()
    firma = re.search(r"^\s*(?:@\w+\s*)*(?:public|private|protected)\s[^\n;=]*\b" + re.escape(nombre_metodo)
                      + r"\s*\([^)]*\)\s*(?:throws [\w., ]+)?\s*\{", texto, flags=re.M) if nombre_metodo else None
    if firma:
        inicio, nivel = firma.end(), 1
        for i in range(inicio, len(texto)):
            if texto[i] == "{":
                nivel += 1
            elif texto[i] == "}":
                nivel -= 1
                if nivel == 0:
                    return texto[inicio:i].strip()
    return texto


def _system_prompt(contexto_diagrama: str, metodo: dict, contexto_clase: str) -> str:
    entidad = metodo.get("entidad", "Entidad")
    service = metodo.get("service", f"{entidad}Service")
    return (
        "Eres un desarrollador senior de Spring Boot 3 / Java 17. Escribes el CUERPO de un método de servicio "
        "que debe compilar a la primera y tener lógica de negocio real y coherente con su nombre.\n\n"
        f"{contexto_diagrama}\n\n"
        f"CLASE: com.proyecto.services.{service} (anotada @Service).\n"
        f"Firma exacta: public {metodo.get('retorno', 'void')} {metodo.get('nombre', 'metodo')}({metodo.get('parametros', '')})\n"
        f"Campos de {service}: SOLO `repository`. Variables: SOLO los parámetros y las que declares.\n"
        "Imports ya presentes: java.util.List, java.util.UUID, java.util.stream.Collectors. Para todo lo demás usa "
        "el nombre completo (java.util.Map, java.math.BigDecimal, java.time.LocalDate, java.util.Optional...).\n\n"
        f"{contexto_clase}\n\n"
        "CÓMO RAZONAR LA LÓGICA:\n"
        "- Deduce la intención por el nombre del método, sus parámetros, el retorno y los atributos de la entidad "
        "(p. ej. calcularTotal -> suma de un campo numérico de los registros; aplicarDescuento(porcentaje) -> "
        "recalcula precios y guarda; buscarPorX -> filtra con stream; contarActivos -> filtra y cuenta).\n"
        "- Si el método modifica datos, persiste con repository.save/saveAll y devuelve lo que pide la firma.\n"
        "- Valida parámetros null (son @RequestParam opcionales) y lanza IllegalArgumentException con un mensaje claro.\n"
        "- Los getters numéricos pueden devolver null: trátalos (p. ej. `x == null ? 0 : x`).\n\n"
        "REGLAS DE SALIDA (obligatorias):\n"
        "1. Responde SOLO con un bloque ```java que contenga las sentencias que van DENTRO de las llaves del método.\n"
        "2. Sin firma, sin clase, sin imports, sin explicaciones.\n"
        "3. Usa ÚNICAMENTE los getters/setters listados arriba; nunca un atributo suelto ni uno inventado.\n"
        "4. Si el retorno no es void, todas las ramas retornan un valor de ese tipo exacto (Double/Integer/Boolean "
        "son wrappers: autoboxing permitido).\n"
        "5. Si de verdad no se puede deducir, el cuerpo es: throw new UnsupportedOperationException(\"<motivo>\");"
    )


async def pedir_codigo_ia(prompt: str, contexto_str: str, client: httpx.AsyncClient, metodo: dict = None,
                          contexto_clase: str = "") -> str:
    metodo = metodo or {}
    texto = await llm_codigo(client, _system_prompt(contexto_str, metodo, contexto_clase), prompt)
    cuerpo = extraer_cuerpo(texto, metodo.get("nombre", ""))
    if not cuerpo:
        raise RuntimeError("la IA devolvió una respuesta vacía")
    return cuerpo


async def corregir_codigo_ia(client: httpx.AsyncClient, contexto_str: str, metodo: dict, contexto_clase: str,
                             codigo: str, errores: list) -> str:
    """Segunda vuelta: la IA recibe su código y los errores reales de javac."""
    user = (
        f"Este cuerpo del método {metodo.get('nombre')} NO compila.\n\n```java\n{codigo}\n```\n\n"
        "Errores del compilador (javac):\n- " + "\n- ".join(errores[:8]) +
        "\n\nDevuelve el cuerpo corregido completo, solo el bloque ```java."
    )
    texto = await llm_codigo(client, _system_prompt(contexto_str, metodo, contexto_clase), user)
    return extraer_cuerpo(texto, metodo.get("nombre", ""))


# ── inyección ─────────────────────────────────────────────────────────────────

async def inyectar_logica_ia(temp_dir: str, diagram_json: dict = None, descripcion_proyecto: str = ""):
    """
    Busca los marcadores @IA_PROMPT del código generado y pide a Kimi (con respaldo) el cuerpo de cada
    método, dándole el código real de la entidad y sus getters para que no invente nada.

    Después COMPILA (si hay Maven): los métodos que no compilan vuelven a la IA con el error de javac
    para una corrección; si aún fallan quedan como TODO, así el backend siempre compila y se despliega.
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

    clases = {t["metodo"]["entidad"]: contexto_entidad(temp_dir, t["metodo"]["entidad"]) for t in tareas}
    limite = asyncio.Semaphore(_MAX_PARALELO)

    async def una(t, client):
        async with limite:
            return await pedir_codigo_ia(t["prompt"], contexto_str, client, t["metodo"], clases[t["metodo"]["entidad"]])

    async with httpx.AsyncClient(timeout=180.0) as client:
        resultados = await asyncio.gather(*(una(t, client) for t in tareas), return_exceptions=True)

    reemplazos_por_archivo = {}
    for n, (tarea, resultado) in enumerate(zip(tareas, resultados)):
        nombre = tarea["metodo"]["nombre"]
        if isinstance(resultado, Exception) or not resultado:
            motivo = str(resultado).splitlines()[0][:150] if resultado else "la IA no respondió"
            print(f"[IA] {tarea['metodo']['service']}.{nombre}: {motivo}")
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

    await asegurar_que_compila_con_ia(temp_dir, contexto_str, clases)


# ── compilación y corrección ─────────────────────────────────────────────────

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


def _errores_por_archivo(salida: str) -> dict:
    """{ruta normalizada: [(línea, mensaje), ...]}"""
    errores = {}
    for ruta, linea, mensaje in _ERROR_JAVA.findall(salida):
        ruta = ruta.strip()
        if re.match(r"^/[A-Za-z]:/", ruta):  # Maven en Windows: /C:/...
            ruta = ruta[1:]
        errores.setdefault(os.path.normcase(os.path.abspath(ruta)), []).append((int(linea), mensaje.strip()))
    return errores


def _bloques_ia(lineas: list) -> list:
    """[(n, línea_inicio, línea_fin)] de los bloques // @IA_BEGIN n .. // @IA_END n (1-indexado)."""
    bloques, abierto = [], None
    for i, l in enumerate(lineas, start=1):
        m = re.match(r"\s*// @IA_(BEGIN|END) (\d+)\s*$", l)
        if m and m.group(1) == "BEGIN":
            abierto = (int(m.group(2)), i)
        elif m and abierto and int(m.group(2)) == abierto[0]:
            bloques.append((abierto[0], abierto[1], i))
            abierto = None
    return bloques


def _bloques_con_error(ruta: str, errores: list) -> list:
    """[(n, inicio, fin, código, [mensajes], metodo)] de los bloques de la IA con errores."""
    if not os.path.isfile(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = f.read().split("\n")
    res = []
    for n, a, b in _bloques_ia(lineas):
        mensajes = [f"línea {l - a}: {m}" for l, m in errores if a <= l <= b]
        if mensajes:
            previa = "\n".join(lineas[:a - 1])
            res.append((n, a, b, "\n".join(lineas[a:b - 1]), mensajes, _contexto_metodo(previa, len(previa), ruta)))
    return res


def _reescribir_bloques(ruta: str, nuevos: dict) -> None:
    """nuevos = {n: código}; reemplaza el contenido de esos bloques."""
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = f.read().split("\n")
    for n, a, b in sorted(_bloques_ia(lineas), key=lambda x: x[1], reverse=True):
        if n in nuevos:
            lineas[a - 1:b] = _bloque(n, nuevos[n]).split("\n")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))


def _reemplazar_bloques_con_error(ruta: str, lineas_error: set) -> int:
    """Cambia por el cuerpo por defecto cada bloque de la IA que contenga una línea con error."""
    malos = _bloques_con_error(ruta, [(l, "") for l in lineas_error])
    if malos:
        _reescribir_bloques(ruta, {n: cuerpo_por_defecto(met["nombre"], "El código generado por la IA no compilaba")
                                   for n, _, _, _, _, met in malos})
    return len(malos)


async def asegurar_que_compila_con_ia(proyecto_dir: str, contexto_str: str = "", clases: dict = None,
                                      rondas_ia: int = 1) -> bool:
    """Compila; los bloques con error van a la IA con el mensaje de javac (rondas_ia veces) y, si siguen
    fallando, pasan a un cuerpo por defecto. Devuelve True si el proyecto termina compilando."""
    if not os.path.isfile(os.path.join(proyecto_dir, "pom.xml")):
        return False
    clases = clases or {}
    ronda = 0
    for _ in range(rondas_ia + 3):
        res = await asyncio.to_thread(_compilar, proyecto_dir)
        if res is None:
            print("[IA] Maven no disponible: no se verificó la compilación del código de la IA.")
            return False
        salida, codigo = res
        if codigo == 0:
            return True
        errores = _errores_por_archivo(salida)
        if not errores:
            print("[IA] La compilación falló sin errores de código (dependencias/JDK): " + salida.strip()[-300:])
            return False
        malos = {ruta: _bloques_con_error(ruta, errs) for ruta, errs in errores.items()}
        malos = {r: b for r, b in malos.items() if b}
        if not malos:
            print("[IA] Errores de compilación fuera del código de la IA:\n" + "\n".join(
                l for l in salida.splitlines() if "[ERROR]" in l)[:1500])
            return False

        if ronda < rondas_ia and _orden_proveedores():
            ronda += 1
            async with httpx.AsyncClient(timeout=180.0) as client:
                pendientes = [(ruta, b) for ruta, bloques in malos.items() for b in bloques]
                arreglos = await asyncio.gather(*(
                    corregir_codigo_ia(client, contexto_str, met, clases.get(met["entidad"], ""), cod, msgs)
                    for _, (n, a, z, cod, msgs, met) in pendientes
                ), return_exceptions=True)
            por_archivo = {}
            for (ruta, (n, *_rest)), arreglo in zip(pendientes, arreglos):
                if isinstance(arreglo, Exception) or not arreglo:
                    met = _rest[-1]
                    arreglo = cuerpo_por_defecto(met["nombre"], "El código generado por la IA no compilaba")
                por_archivo.setdefault(ruta, {})[n] = arreglo
            for ruta, nuevos in por_archivo.items():
                _reescribir_bloques(ruta, nuevos)
            print(f"[IA] {len(pendientes)} método(s) no compilaban: se pidió a la IA corregirlos con el error de javac.")
        else:
            total = sum(_reemplazar_bloques_con_error(r, {a for a, _ in errores[r]}) for r in malos)
            print(f"[IA] {total} método(s) siguen sin compilar: se dejaron como TODO.")
    return False


def asegurar_que_compila(proyecto_dir: str, intentos: int = 3) -> bool:
    """Versión sin IA (solo pasa a TODO lo que no compila). Se mantiene por compatibilidad."""
    return asyncio.run(asegurar_que_compila_con_ia(proyecto_dir, rondas_ia=0))
