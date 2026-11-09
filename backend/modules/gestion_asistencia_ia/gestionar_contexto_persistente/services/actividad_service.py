"""
CU40: actividad del equipo en la pizarra.

Lo que importa es QUIÉN CAMBIÓ LA PIZARRA:
  - cambios a mano y restauraciones → los hizo su autor;
  - cambios de la IA → los puso en la pizarra quien los APROBÓ (y se anota quién los pidió);
  - correcciones → quién las señaló y quién las resolvió.
Además: tareas y comentarios por miembro.
"""
import json
import re
import time
import unicodedata
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

MAX_EVENTOS = 200


def _pedido_visible(cmd: Optional[str]) -> str:
    """Solo lo que escribió la persona: quita la cabecera y las directrices que el sistema añade al prompt."""
    t = (cmd or "").strip()
    t = re.split(r"\n\s*\n\s*(?:DIRECTRICES|INSTRUCCIONES|REGLAS|CONTEXTO)\b", t, maxsplit=1)[0]
    lineas = [l.strip() for l in t.splitlines() if l.strip()]
    if len(lineas) > 1 and re.fullmatch(r"[A-ZÁÉÍÓÚÑ0-9 ,./()-]+:", lineas[0]):
        lineas = lineas[1:]
    t = " ".join(lineas)
    return t[:180] + ("…" if len(t) > 180 else "")


def _clave(nombre: Optional[str]) -> str:
    n = unicodedata.normalize("NFKD", (nombre or "").strip()).encode("ascii", "ignore").decode().lower()
    return n or "(sin nombre)"


def _limpio(nombre: Optional[str]) -> str:
    return (nombre or "").strip() or "(sin nombre)"


def _seg(valor: Any) -> Optional[int]:
    """Fecha en segundos (las correcciones guardan milisegundos)."""
    try:
        v = int(valor)
    except (TypeError, ValueError):
        return None
    return v // 1000 if v > 10**11 else v


CLAVES = ("cambios_manuales", "restauraciones", "ia_aprobados", "ia_rechazados",
          "correcciones_senaladas", "correcciones_resueltas",
          "tareas_asignadas", "tareas_completadas", "horas_estimadas", "horas_completadas", "comentarios")


async def contribucion(db: AsyncSession, proyecto_id: int, dias: Optional[int] = 30) -> Dict[str, Any]:
    desde = int(time.time()) - dias * 86400 if dias else 0
    miembros: Dict[str, Dict[str, Any]] = {}
    eventos: List[Dict[str, Any]] = []

    def m(nombre: Optional[str]) -> Dict[str, Any]:
        k = _clave(nombre)
        if k not in miembros:
            miembros[k] = {"nombre": _limpio(nombre), **{c: 0 for c in CLAVES}}
        return miembros[k]

    # ── Historial: cambios a mano y cambios de la IA ────────────────────────
    versiones = (await db.execute(text(
        "SELECT id, ts, autor, intent, estado_propuesta, decidida_por, decidida_en, cmd, resumen, delta "
        "FROM versiones_contexto_ia WHERE proyecto_id = :p AND ts >= :d ORDER BY ts DESC, id DESC"
    ), {"p": proyecto_id, "d": desde})).all()
    pendientes = 0
    for vid, ts, autor, intent, estado, decidida_por, decidida_en, cmd, resumen, delta in versiones:
        intent = (intent or "").upper()
        base = {"version_id": vid, "delta": delta or "", "resumen": (resumen or "").strip()[:200]}
        if intent in ("MANUAL", "RESTAURAR"):
            m(autor)["cambios_manuales" if intent == "MANUAL" else "restauraciones"] += 1
            eventos.append({**base, "tipo": "manual" if intent == "MANUAL" else "restaurar",
                            "quien": _limpio(autor), "ts": ts})
        elif estado in ("aprobada", "rechazada"):
            # El cambio de la IA lo pone (o lo descarta) quien decide
            quien = decidida_por or autor
            m(quien)["ia_aprobados" if estado == "aprobada" else "ia_rechazados"] += 1
            eventos.append({**base, "tipo": "ia_aprobada" if estado == "aprobada" else "ia_rechazada",
                            "quien": _limpio(quien), "pedido_por": _limpio(autor), "pedido": _pedido_visible(cmd),
                            "ts": int(decidida_en.timestamp()) if decidida_en else ts})
        elif estado == "pendiente":
            pendientes += 1
            eventos.append({**base, "tipo": "ia_pendiente", "quien": None, "pedido_por": _limpio(autor),
                            "pedido": _pedido_visible(cmd), "ts": ts})
        else:
            # Versiones de antes del flujo aprobar/rechazar: se aplicaron al pedirlas
            m(autor)["ia_aprobados"] += 1
            eventos.append({**base, "tipo": "ia_directa", "quien": _limpio(autor), "pedido_por": _limpio(autor),
                            "pedido": _pedido_visible(cmd), "ts": ts})

    # ── Correcciones (viven en el lienzo del proyecto) ───────────────────────
    lienzo_txt = (await db.execute(text("SELECT lienzo_json FROM proyectos WHERE id = :p"), {"p": proyecto_id})).scalar()
    try:
        lienzo = json.loads(lienzo_txt) if isinstance(lienzo_txt, str) else (lienzo_txt or {})
    except (TypeError, ValueError):
        lienzo = {}
    clases = {str(n.get("id")): n.get("nombre") or "" for n in (lienzo.get("nodes") or []) if isinstance(n, dict)}
    correcciones = lienzo.get("correcciones") or {}
    if isinstance(correcciones, dict):
        for target, lista in correcciones.items():
            for c in (lista or []):
                if not isinstance(c, dict):
                    continue
                clase = clases.get(str(c.get("targetId") or target)) or "General"
                texto = str(c.get("texto") or "")[:200]
                creada = _seg(c.get("fecha"))
                if creada is not None and creada >= desde:
                    m(c.get("autorNombre"))["correcciones_senaladas"] += 1
                    eventos.append({"tipo": "correccion_senalada", "quien": _limpio(c.get("autorNombre")),
                                    "clase": clase, "texto": texto, "ts": creada})
                resuelta = _seg(c.get("fechaResolucion"))
                if c.get("estado") == "resuelta" and resuelta is not None and resuelta >= desde:
                    m(c.get("resueltoPorNombre"))["correcciones_resueltas"] += 1
                    eventos.append({"tipo": "correccion_resuelta", "quien": _limpio(c.get("resueltoPorNombre")),
                                    "clase": clase, "texto": texto, "senalada_por": _limpio(c.get("autorNombre")),
                                    "ts": resuelta})

    # ── Tareas y comentarios ────────────────────────────────────────────────
    tareas = (await db.execute(text(
        "SELECT u.nombre, count(*), coalesce(sum(CASE WHEN t.completada THEN 1 ELSE 0 END), 0), "
        "coalesce(sum(t.estimacion_horas), 0), coalesce(sum(CASE WHEN t.completada THEN t.estimacion_horas ELSE 0 END), 0) "
        "FROM tareas_ia t JOIN usuarios u ON u.id = t.usuario_id WHERE t.proyecto_id = :p GROUP BY u.nombre"
    ), {"p": proyecto_id})).all()
    for nombre, total, hechas, horas, horas_hechas in tareas:
        fila = m(nombre)
        fila["tareas_asignadas"] += int(total)
        fila["tareas_completadas"] += int(hechas)
        fila["horas_estimadas"] += int(horas or 0)
        fila["horas_completadas"] += int(horas_hechas or 0)

    comentarios = (await db.execute(text(
        "SELECT autor_nombre, count(*) FROM diagram_element_comments "
        "WHERE proyecto_id = :p AND created_at >= to_timestamp(:d) GROUP BY autor_nombre"
    ), {"p": proyecto_id, "d": desde})).all()
    for autor, n in comentarios:
        if (autor or "").startswith("IA"):   # "IA (aprobado por X)": no es aporte de una persona
            continue
        m(autor)["comentarios"] += int(n)

    # ── Resultado ───────────────────────────────────────────────────────────
    lista = list(miembros.values())
    for f in lista:
        f["cambios_pizarra"] = f["cambios_manuales"] + f["restauraciones"] + f["ia_aprobados"] + f["correcciones_resueltas"]
        f["total"] = f["cambios_pizarra"] + f["ia_rechazados"] + f["correcciones_senaladas"] + f["tareas_completadas"] + f["comentarios"]
    lista = [f for f in lista if f["total"] or f["tareas_asignadas"]]
    lista.sort(key=lambda f: (-f["cambios_pizarra"], -f["total"], f["nombre"].lower()))

    totales: Dict[str, Any] = {k: sum(f[k] for f in lista) for k in CLAVES + ("cambios_pizarra",)}
    totales["ia_pendientes"] = pendientes
    eventos.sort(key=lambda e: e["ts"] or 0, reverse=True)
    return {"dias": dias, "miembros": lista, "totales": totales, "eventos": eventos[:MAX_EVENTOS]}
