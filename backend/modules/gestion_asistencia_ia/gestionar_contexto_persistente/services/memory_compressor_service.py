import re
import time
from typing import List, Dict, Any, Tuple
from backend.modules.gestion_asistencia_ia.generar_diagrama_prompt.services.prompt_compressor import HybridPromptCompressor

_prompt_compressor = HybridPromptCompressor()


DOMINIOS_KEYWORDS = {
    "Sistema Universitario / Académico": [
        "estudiante", "docente", "profesor", "alumno", "curso", "materia", "carrera",
        "facultad", "inscripcion", "calificacion", "nota", "tarea", "entrega", "aula"
    ],
    "Comercio Electrónico / Ventas": [
        "cliente", "pedido", "orden", "producto", "carrito", "pago", "factura",
        "detalle", "inventario", "envio", "categoria"
    ],
    "Gestión Hospitalaria / Salud": [
        "paciente", "medico", "doctor", "cita", "consulta", "historia_clinica",
        "tratamiento", "receta", "medicamento", "especialidad"
    ],
    "Finanzas / Banca": [
        "cuenta", "transaccion", "transferencia", "banco", "saldo", "tarjeta",
        "prestamo", "interes", "movimiento"
    ],
    "Gestión de Proyectos / Tareas": [
        "tarea", "proyecto", "sprint", "equipo", "colaborador", "hito", "incidencia",
        "bug", "tablero", "responsable"
    ]
}


def detectar_dominio(texto: str, dominio_actual: str = "Sistema de Software") -> str:
    """Infiere el dominio del proyecto a partir de palabras clave en el texto."""
    t_lower = texto.lower()
    for dom, kws in DOMINIOS_KEYWORDS.items():
        if any(kw in t_lower for kw in kws):
            return dom
    return dominio_actual or "Sistema de Software"


def comprimir_instruccion(prompt: str) -> str:
    """
    Condensa la instrucción del usuario utilizando raíces morfológicas y operadores universales
    (FIX, EDIT, ADD, DEL, LINK, CLS, TBL, etc.) eliminando relleno y artículos.
    """
    if not prompt:
        return ""
    compressed = _prompt_compressor.compress(prompt)
    if len(compressed) > 120:
        return compressed[:117] + "..."
    return compressed


def generar_delta_compacto(added: List[str], updated: List[str], deleted: List[str]) -> str:
    """Genera una firma de delta ultra-compacta (+Clase, -Clase, ~Clase) omitiendo identificadores dummy o sintéticos."""
    JUNK = {
        "node_x", "node_1", "node_2", "node_3", "node_4", "node_5", "node_6",
        "diagrama", "eliminadas", "borradas", "clases", "nodo", "tabla"
    }
    clean_added = [a for a in added if a and not re.match(r"^node_\w+$", str(a).lower()) and str(a).lower() not in JUNK]
    clean_updated = [u for u in updated if u and not re.match(r"^node_\w+$", str(u).lower()) and str(u).lower() not in JUNK]
    clean_deleted = [d for d in deleted if d and not re.match(r"^node_\w+$", str(d).lower()) and str(d).lower() not in JUNK]

    parts: List[str] = []
    if clean_added:
        parts.append("+" + ",".join(clean_added[:5]))
    if clean_updated:
        parts.append("~" + ",".join(clean_updated[:5]))
    if clean_deleted:
        parts.append("-" + ",".join(clean_deleted[:5]))
    return " | ".join(parts) if parts else "sin_cambios"


def compilar_contexto_para_llm(
    proyecto_id: int,
    dominio: str,
    resumen_acumulado: str,
    historial: List[Dict[str, Any]],
    correcciones: List[Dict[str, Any]],
    snapshot_dsl: str
) -> Tuple[str, int, int]:
    """
    Compila el contexto de memoria a un bloque de texto ultra-denso
    listo para inyección directa en el prompt del LLM.
    Retorna: (bloque_texto, tokens_estimados, tokens_ahorrados_estimados).
    """
    lineas: List[str] = [
        f"[MEMORIA DEL PROYECTO #{proyecto_id}]",
        f"Dominio: {dominio or 'Sistema de Software'}"
    ]

    if resumen_acumulado:
        lineas.append(f"Estado Acumulado: {resumen_acumulado}")

    # Últimas 5 interacciones episódicas (rolling memory)
    recientes = historial[-5:] if historial else []
    if recientes:
        lineas.append("Historial Episódico Reciente:")
        for ev in recientes:
            intent = ev.get("intent", "ACTION")
            cmd = ev.get("cmd", "")
            summary = ev.get("summary", "")
            delta = ev.get("delta", "")
            lineas.append(f"• [{intent}] {cmd} -> {summary} (Δ: {delta})")

    # Correcciones activas pendientes
    abiertas = [c for c in correcciones if c.get("estado", "abierta") == "abierta"]
    if abiertas:
        lineas.append(f"Correcciones / Tareas Pendientes ({len(abiertas)}):")
        for c in abiertas[:6]:
            target = c.get("target", "General")
            text = c.get("text", "")
            lineas.append(f"• [{target}]: {text}")

    if snapshot_dsl:
        # DSL ultra-comprimido en una sola línea
        clean_dsl = snapshot_dsl.replace("\n", ";").strip()
        lineas.append(f"Diagrama Actual: {clean_dsl}")

    bloque = "\n".join(lineas)
    
    # Estimación de tokens: ~4 caracteres por token
    tokens_estimados = max(1, len(bloque) // 4)
    
    # Estimación de lo que habría ocupado el chat crudo y JSON completos (~4500 tokens)
    tokens_crudos_equivalentes = 4500 + (len(historial) * 200)
    tokens_ahorrados = max(0, tokens_crudos_equivalentes - tokens_estimados)

    return bloque, tokens_estimados, tokens_ahorrados

