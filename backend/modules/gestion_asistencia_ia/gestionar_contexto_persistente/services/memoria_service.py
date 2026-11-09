"""
Memoria del proyecto al estilo Engram (https://github.com/Gentleman-Programming/engram).

En lugar de mandarle a la IA "las últimas N cosas que pasaron", se guardan
observaciones elegidas (decisiones, restricciones, convenciones, correcciones y
rechazos), cada una con un tema estable (topic_key). Antes de cada pedido se
buscan las que son relevantes para ese pedido.

Reglas:
  - Mismo tema → la observación nueva REEMPLAZA a la anterior (que queda como
    historial, vigente=False). Un solo recuerdo vigente por tema.
  - Si lo reemplazado lo escribió una persona (origen "manual") y lo nuevo es
    automático, queda en_conflicto: una persona decide cuál vale.
  - Los rechazos van en su propio tema ("rechazos/<clase>") para no borrar el
    diseño aprobado de esa clase. Aprobar algo de la clase da de baja su rechazo.
"""
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.gestion_asistencia_ia.models import MemoriaIA

TIPOS = ("decision", "restriccion", "convencion", "correccion", "rechazo")
# Siempre se envían a la IA (son reglas del proyecto)
TIPOS_FIJOS = ("restriccion", "convencion")
MAX_FIJAS = 4
MAX_RELEVANTES = 6
MAX_OBS_POR_PROPUESTA = 10

_PALABRAS_RESTRICCION = re.compile(r"\b(nunca|no debe|no deben|prohib|siempre|obligatori|debe|deben)\w*", re.I)
_VACIAS = {
    "para", "como", "con", "los", "las", "una", "uno", "unos", "unas", "del", "que", "por", "sus",
    "este", "esta", "esto", "agrega", "agregar", "crea", "crear", "pon", "poner", "haz", "hacer",
    "diag", "clase", "clases", "diagrama", "favor", "quiero", "necesito",
}


def slug(texto: str, max_len: int = 60) -> str:
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_").lower()
    return t[:max_len] or "general"


def tema_entidad(nombre: str) -> str:
    return f"entidades/{slug(nombre)}"


def tema_rechazo(nombre: str) -> str:
    return f"rechazos/{slug(nombre)}"


def _palabras(texto: str) -> List[str]:
    vistas, out = set(), []
    for w in re.findall(r"[0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ_]{3,}", texto or ""):
        lw = w.lower()
        if lw in _VACIAS or lw in vistas:
            continue
        vistas.add(lw)
        out.append(lw)
    return out[:20]


def a_dict(m: MemoriaIA) -> Dict[str, Any]:
    return dict(
        id=m.id, tipo=m.tipo, topic_key=m.topic_key, titulo=m.titulo, que=m.que, por_que=m.por_que,
        donde=m.donde, aprendido=m.aprendido, origen=m.origen, autor=m.autor, vigente=m.vigente,
        en_conflicto=m.en_conflicto, reemplaza_id=m.reemplaza_id, version_id=m.version_id,
        creada=int(m.created_at.timestamp()) if m.created_at else 0,
        actualizada=int(m.updated_at.timestamp()) if m.updated_at else 0,
    )


# ─── Guardar ────────────────────────────────────────────────────────────────

async def guardar(
    db: AsyncSession,
    proyecto_id: int,
    *,
    tipo: str,
    topic_key: str,
    titulo: str,
    que: str,
    por_que: str = "",
    donde: str = "",
    aprendido: str = "",
    origen: str = "manual",
    version_id: Optional[int] = None,
    autor: Optional[str] = None,
    confirmar: bool = True,
) -> MemoriaIA:
    """Crea la observación o reemplaza la vigente del mismo tema."""
    tipo = tipo if tipo in TIPOS else "decision"
    topic_key = (topic_key or "general").strip()[:120]

    actual = (await db.execute(
        select(MemoriaIA).where(
            MemoriaIA.proyecto_id == proyecto_id,
            MemoriaIA.topic_key == topic_key,
            MemoriaIA.vigente.is_(True),
        )
    )).scalars().first()

    # Lo mismo otra vez: no se duplica
    if actual and (actual.tipo, actual.que.strip(), actual.aprendido.strip()) == (tipo, que.strip(), aprendido.strip()):
        return actual

    conflicto = bool(actual and actual.origen == "manual" and origen != "manual")
    if actual:
        actual.vigente = False
        await db.flush()   # libera el índice único "un vigente por tema" antes de insertar

    nueva = MemoriaIA(
        proyecto_id=proyecto_id, tipo=tipo, topic_key=topic_key, titulo=(titulo or topic_key)[:200],
        que=(que or "")[:4000], por_que=(por_que or "")[:2000], donde=(donde or "")[:500],
        aprendido=(aprendido or "")[:2000], origen=origen, version_id=version_id, autor=autor,
        vigente=True, reemplaza_id=actual.id if actual else None, en_conflicto=conflicto,
    )
    db.add(nueva)
    if confirmar:
        await db.commit()
        await db.refresh(nueva)
    else:
        await db.flush()
    return nueva


async def dar_de_baja_temas(db: AsyncSession, proyecto_id: int, temas: Iterable[str]) -> int:
    temas = list(temas)
    if not temas:
        return 0
    filas = (await db.execute(
        select(MemoriaIA).where(
            MemoriaIA.proyecto_id == proyecto_id,
            MemoriaIA.topic_key.in_(temas),
            MemoriaIA.vigente.is_(True),
        )
    )).scalars().all()
    for f in filas:
        f.vigente = False
    return len(filas)


def desde_texto(texto: str) -> Dict[str, str]:
    """
    "/recordar entidades/cliente: el email es único" → tema explícito.
    "/recordar los ids son UUID" → tema derivado del texto.
    Restricción si suena a regla ("nunca", "siempre", "debe", "prohibido"…), si no convención.
    """
    texto = (texto or "").strip()
    tema, contenido = None, texto
    m = re.match(r"^\s*([\w\-]+(?:/[\w\-]+)+)\s*:\s*(.+)$", texto, re.S)
    if m:
        tema, contenido = m.group(1).lower(), m.group(2).strip()
    tipo = "restriccion" if _PALABRAS_RESTRICCION.search(contenido) else "convencion"
    if not tema:
        tema = f"{'reglas' if tipo == 'restriccion' else 'convenciones'}/{slug(' '.join(contenido.split()[:6]), 40)}"
    titulo = contenido if len(contenido) <= 80 else contenido[:77] + "…"
    return dict(tipo=tipo, topic_key=tema, titulo=titulo, que=contenido,
                aprendido="Regla indicada por el equipo; respetarla siempre." if tipo == "restriccion"
                else "Convención del equipo; seguirla salvo que se pida otra cosa.")


async def desde_propuesta(db: AsyncSession, version: Any, aprobada: bool, decidida_por: Optional[str]) -> int:
    """Convierte una propuesta decidida en observaciones. Devuelve cuántas guardó."""
    prop = version.propuesta or {}
    tipo_prop = prop.get("tipo") or "diagrama"
    pedido = (version.cmd or "").strip()[:300]
    origen = "aprobacion" if aprobada else "rechazo"
    obs: List[Dict[str, Any]] = []

    if tipo_prop == "roles":
        lineas = [
            f"{r.get('nombre')} → {r.get('rol_ia') or 'Desarrollador'}"
            + (f" ({', '.join(r.get('clases_asignadas') or [])})" if r.get("clases_asignadas") else "")
            for r in (prop.get("roles") or [])
        ]
        if lineas:
            obs.append(dict(
                tipo="decision" if aprobada else "rechazo",
                topic_key="equipo/roles" if aprobada else "rechazos/equipo_roles",
                titulo="Reparto de roles del equipo",
                que="; ".join(lineas), donde="Equipo",
                aprendido="Usar este reparto de roles al asignar trabajo." if aprobada
                else "El equipo rechazó este reparto de roles; no repetirlo igual.",
            ))
    elif tipo_prop == "tareas":
        titulos = [t.get("titulo") for t in (prop.get("tareas") or []) if t.get("titulo")]
        if titulos:
            obs.append(dict(
                tipo="decision" if aprobada else "rechazo",
                topic_key="equipo/tareas" if aprobada else "rechazos/equipo_tareas",
                titulo=f"Plan de tareas ({len(titulos)})",
                que="; ".join(titulos[:15]), donde="Equipo",
                aprendido="Estas tareas ya están asignadas; no volver a proponerlas." if aprobada
                else "El equipo rechazó estas tareas; no volver a proponerlas igual.",
            ))
    else:
        for n in (prop.get("nodes") or [])[:MAX_OBS_POR_PROPUESTA]:
            nombre = n.get("name") or n.get("nombre")
            if not nombre:
                continue
            attrs = [a if isinstance(a, str) else f"{a.get('nombre')}:{a.get('tipo')}"
                     for a in (n.get("attributes") or n.get("atributos") or [])]
            mets = [m if isinstance(m, str) else m.get("nombre", "")
                    for m in (n.get("methods") or n.get("metodos") or [])]
            detalle = ", ".join(attrs[:15]) + (f" | métodos: {', '.join(mets[:8])}" if mets else "")
            if aprobada:
                obs.append(dict(
                    tipo="decision", topic_key=tema_entidad(nombre), titulo=f"Clase {nombre}",
                    que=f"{nombre}: {detalle}" if detalle else nombre, donde=nombre,
                    aprendido="Diseño aceptado por el equipo; mantenerlo salvo que se pida cambiarlo.",
                ))
            else:
                obs.append(dict(
                    tipo="rechazo", topic_key=tema_rechazo(nombre), titulo=f"Propuesta rechazada: {nombre}",
                    que=f"Se propuso {nombre}: {detalle}" if detalle else f"Se propuso {nombre}", donde=nombre,
                    aprendido="El equipo rechazó esta propuesta; no volver a sugerirla igual sin que lo pidan.",
                ))
        for d in (prop.get("deletedNodes") or [])[:MAX_OBS_POR_PROPUESTA]:
            nombre = d if isinstance(d, str) else (d.get("name") or d.get("id") or "")
            if not nombre:
                continue
            obs.append(dict(
                tipo="decision" if aprobada else "rechazo",
                topic_key=tema_entidad(nombre) if aprobada else tema_rechazo(nombre),
                titulo=f"Eliminar {nombre}",
                que=f"Se eliminó la clase {nombre}" if aprobada else f"Se propuso eliminar {nombre} y se rechazó",
                donde=nombre,
                aprendido="La clase ya no forma parte del modelo." if aprobada
                else f"El equipo quiere conservar {nombre}; no proponer eliminarla.",
            ))

    if aprobada:
        # Aprobar algo de una clase deja sin efecto su rechazo anterior
        nombres = [o["donde"] for o in obs if o["topic_key"].startswith("entidades/")]
        await dar_de_baja_temas(db, version.proyecto_id, [tema_rechazo(n) for n in nombres])

    for o in obs[:MAX_OBS_POR_PROPUESTA]:
        await guardar(
            db, version.proyecto_id, por_que=f"Pedido: {pedido}" if pedido else "",
            origen=origen, version_id=version.id, autor=decidida_por, confirmar=False, **o,
        )
    await db.commit()
    return len(obs)


# ─── Buscar ─────────────────────────────────────────────────────────────────

async def buscar_relevantes(
    db: AsyncSession, proyecto_id: int, consulta: str = "", limite: int = MAX_RELEVANTES
) -> List[MemoriaIA]:
    """
    Reglas fijas (restricciones / convenciones) + observaciones relevantes para el pedido
    (búsqueda en español y clases mencionadas). Sin pedido: las más recientes.
    """
    base = (MemoriaIA.proyecto_id == proyecto_id, MemoriaIA.vigente.is_(True))
    fijas = list((await db.execute(
        select(MemoriaIA).where(*base, MemoriaIA.tipo.in_(TIPOS_FIJOS))
        .order_by(MemoriaIA.updated_at.desc()).limit(MAX_FIJAS)
    )).scalars().all())
    ids_fijas = [m.id for m in fijas]

    palabras = _palabras(consulta)
    relevantes: List[MemoriaIA] = []
    if palabras:
        consulta_ts = func.to_tsquery("spanish", " | ".join(palabras))
        temas = [tema_entidad(p) for p in palabras] + [tema_rechazo(p) for p in palabras]
        stmt = (
            select(MemoriaIA).where(
                *base,
                ~MemoriaIA.id.in_(ids_fijas) if ids_fijas else true(),
                or_(MemoriaIA.busqueda.op("@@")(consulta_ts), MemoriaIA.topic_key.in_(temas)),
            )
            .order_by(func.ts_rank(MemoriaIA.busqueda, consulta_ts).desc(), MemoriaIA.updated_at.desc())
            .limit(limite)
        )
        relevantes = list((await db.execute(stmt)).scalars().all())

    if not relevantes:
        stmt = select(MemoriaIA).where(*base, ~MemoriaIA.id.in_(ids_fijas) if ids_fijas else true())
        relevantes = list((await db.execute(
            stmt.order_by(MemoriaIA.updated_at.desc()).limit(min(3, limite))
        )).scalars().all())

    return fijas + relevantes


# ─── Gestión desde el modal ─────────────────────────────────────────────────

async def listar(db: AsyncSession, proyecto_id: int, incluir_historial: bool = False) -> List[MemoriaIA]:
    stmt = select(MemoriaIA).where(MemoriaIA.proyecto_id == proyecto_id)
    if not incluir_historial:
        stmt = stmt.where(MemoriaIA.vigente.is_(True))
    stmt = stmt.order_by(MemoriaIA.vigente.desc(), MemoriaIA.en_conflicto.desc(), MemoriaIA.updated_at.desc())
    return list((await db.execute(stmt)).scalars().all())


async def obtener(db: AsyncSession, proyecto_id: int, memoria_id: int) -> Optional[MemoriaIA]:
    return (await db.execute(
        select(MemoriaIA).where(MemoriaIA.id == memoria_id, MemoriaIA.proyecto_id == proyecto_id)
    )).scalars().first()


async def editar(db: AsyncSession, memoria: MemoriaIA, campos: Dict[str, Any]) -> MemoriaIA:
    """Edición humana en el lugar (no crea versión nueva) y deja de estar en conflicto."""
    for k in ("tipo", "titulo", "que", "por_que", "donde", "aprendido"):
        if campos.get(k) is not None:
            setattr(memoria, k, campos[k] if k != "tipo" or campos[k] in TIPOS else memoria.tipo)
    memoria.origen = "manual"
    memoria.en_conflicto = False
    await db.commit()
    await db.refresh(memoria)
    return memoria


async def eliminar(db: AsyncSession, memoria: MemoriaIA) -> None:
    await db.delete(memoria)
    await db.commit()


async def resolver_conflicto(db: AsyncSession, memoria: MemoriaIA, mantener_nueva: bool) -> MemoriaIA:
    """Mantener la nueva, o volver a la anterior (la escrita a mano)."""
    if mantener_nueva or not memoria.reemplaza_id:
        memoria.en_conflicto = False
        await db.commit()
        await db.refresh(memoria)
        return memoria
    anterior = await obtener(db, memoria.proyecto_id, memoria.reemplaza_id)
    memoria.vigente = False
    memoria.en_conflicto = False
    await db.flush()
    if anterior:
        anterior.vigente = True
        await db.commit()
        await db.refresh(anterior)
        return anterior
    await db.commit()
    return memoria


def acumular_resumen(previo: str, nuevo: str, max_chars: int = 700) -> str:
    """El resumen del proyecto acumula (antes se pisaba con el último resumen de la IA)."""
    frases: List[str] = []
    for texto in (previo or "", nuevo or ""):
        for f in re.split(r"(?<=[.!?])\s+", texto.strip()):
            f = f.strip()
            if f and f not in frases:
                frases.append(f)
    resultado = " ".join(frases)
    while len(resultado) > max_chars and len(frases) > 1:
        frases.pop(0)            # se descarta lo más antiguo
        resultado = " ".join(frases)
    return resultado[-max_chars:]
