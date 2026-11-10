"""
CU39: notificaciones.

Cómo se generan, sin tocar cada servicio:
  1. `after_flush` (SQLAlchemy) mira lo que se acaba de escribir: tareas nuevas, solicitudes para unirse,
     invitados aprobados, propuestas de la IA y comentarios. Guarda los eventos en `session.info`.
  2. `after_commit` los entrega a una tarea en segundo plano (si hay rollback, se descartan).
  3. La tarea abre su propia sesión, decide a quién avisar, guarda las notificaciones y, si Firebase
     está configurado, envía el push. Un fallo aquí nunca rompe la operación original.

Los eventos que no pasan por el ORM (p. ej. el UPDATE atómico de aprobar/rechazar) usan `encolar()`.
"""
import asyncio
import logging
import os
import unicodedata
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import event, inspect, text
from sqlalchemy.orm import Session

from backend.core.config import settings

log = logging.getLogger("notificaciones")
_CLAVE = "_notif_eventos"
_tareas_vivas: set = set()   # referencias para que el recolector no cancele las tareas en curso


def _norm(nombre: Optional[str]) -> str:
    return unicodedata.normalize("NFKD", (nombre or "").strip()).encode("ascii", "ignore").decode().lower()


def _corto(texto: Optional[str], n: int = 120) -> str:
    t = " ".join((texto or "").split())
    return t[:n] + ("…" if len(t) > n else "")


# ─── Captura de eventos ─────────────────────────────────────────────────────

def encolar(session: Any, evento: Dict[str, Any]) -> None:
    """Agrega un evento a la sesión; se procesa solo si la transacción se confirma."""
    sync = getattr(session, "sync_session", session)
    sync.info.setdefault(_CLAVE, []).append(evento)


def _cambio(obj: Any, attr: str):
    h = inspect(obj).attrs[attr].history
    return (h.deleted[0] if h.deleted else None), (h.added[0] if h.added else None)


@event.listens_for(Session, "after_flush")
def _al_escribir(session: Session, _ctx) -> None:
    # Imports perezosos: evitan ciclos al importar los modelos
    from backend.modules.gestion_asistencia_ia.models import VersionContextoIA
    from backend.modules.gestion_modelado.models import ComentarioElemento
    from backend.modules.gestion_proyectos.models import ColaboradorProyecto
    from backend.modules.gestion_usuarios.models import TareaIA

    eventos: List[Dict[str, Any]] = []
    for obj in session.new:
        if isinstance(obj, TareaIA) and obj.usuario_id:
            eventos.append({"tipo": "tarea_asignada", "proyecto_id": obj.proyecto_id,
                            "usuario_id": obj.usuario_id, "titulo": obj.titulo})
        elif isinstance(obj, ColaboradorProyecto) and obj.estado == "pendiente":
            eventos.append({"tipo": "solicitud_union", "proyecto_id": obj.proyecto_id, "usuario_id": obj.usuario_id})
        elif isinstance(obj, VersionContextoIA) and obj.estado_propuesta == "pendiente":
            eventos.append({"tipo": "propuesta_pendiente", "proyecto_id": obj.proyecto_id, "version_id": obj.id,
                            "autor": obj.autor, "resumen": obj.resumen or obj.cmd})
        elif isinstance(obj, ComentarioElemento) and not (obj.autor_nombre or "").startswith("IA"):
            eventos.append({"tipo": "comentario", "proyecto_id": obj.proyecto_id, "autor_id": obj.autor_id,
                            "autor": obj.autor_nombre, "texto": obj.texto})
    for obj in session.dirty:
        if isinstance(obj, ColaboradorProyecto):
            antes, ahora = _cambio(obj, "estado")
            if ahora == "aprobado" and antes != "aprobado":
                eventos.append({"tipo": "solicitud_aprobada", "proyecto_id": obj.proyecto_id, "usuario_id": obj.usuario_id})
    if eventos:
        session.info.setdefault(_CLAVE, []).extend(eventos)


def programar(eventos: List[Dict[str, Any]]) -> None:
    """Procesa eventos ya confirmados en segundo plano (para operaciones que no pasan por el ORM)."""
    if not eventos:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    tarea = loop.create_task(_procesar_seguro(eventos))
    _tareas_vivas.add(tarea)
    tarea.add_done_callback(_tareas_vivas.discard)


@event.listens_for(Session, "after_commit")
def _al_confirmar(session: Session) -> None:
    programar(session.info.pop(_CLAVE, None) or [])


@event.listens_for(Session, "after_rollback")
def _al_deshacer(session: Session) -> None:
    session.info.pop(_CLAVE, None)


# ─── Destinatarios y mensajes ───────────────────────────────────────────────

async def _miembros(db, proyecto_id: int) -> List[Dict[str, Any]]:
    filas = (await db.execute(text(
        "SELECT u.id, u.nombre, c.rol_proyecto, c.permiso FROM colaboradores_proyecto c JOIN usuarios u ON u.id = c.usuario_id "
        "WHERE c.proyecto_id = :p AND c.estado = 'aprobado'"
    ), {"p": proyecto_id})).all()
    # puede_aprobar: anfitrión o editor (CU38); un lector no decide propuestas
    return [{"id": i, "nombre": n, "rol": r, "puede_aprobar": r == "anfitrion" or (pm or "edit") != "view"}
            for i, n, r, pm in filas]


async def _nombre(db, tabla_sql: str, id_: Any) -> str:
    fila = (await db.execute(text(tabla_sql), {"i": id_})).first()
    return (fila[0] if fila else "") or ""


async def _construir(db, ev: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Devuelve las notificaciones (una por destinatario) para un evento."""
    pid = ev.get("proyecto_id")
    proyecto = await _nombre(db, "SELECT nombre FROM proyectos WHERE id = :i", pid) if pid else ""
    url = f"/diagrama/{pid}" if pid else "/dashboard"
    tipo = ev["tipo"]
    salida: List[Dict[str, Any]] = []

    def para(usuarios: Iterable[int], titulo: str, mensaje: str, destino: str = url):
        for uid in dict.fromkeys(u for u in usuarios if u):
            salida.append(dict(usuario_id=uid, proyecto_id=pid, tipo=tipo, titulo=titulo[:160],
                               mensaje=mensaje, url=destino))

    if tipo == "tarea_asignada":
        para([ev["usuario_id"]], f"Nueva tarea en {proyecto}", _corto(ev.get("titulo")))

    elif tipo == "solicitud_union":
        quien = await _nombre(db, "SELECT nombre FROM usuarios WHERE id = :i", ev["usuario_id"]) or "Alguien"
        anfitriones = [m["id"] for m in await _miembros(db, pid) if m["rol"] == "anfitrion"]
        para(anfitriones, f"{quien} quiere unirse a {proyecto}", "Apruébalo o recházalo desde la sala.")

    elif tipo == "solicitud_aprobada":
        rol = (await db.execute(text(
            "SELECT rol_proyecto FROM colaboradores_proyecto WHERE proyecto_id = :p AND usuario_id = :u"
        ), {"p": pid, "u": ev["usuario_id"]})).scalar()
        if rol != "anfitrion":   # el creador entra aprobado desde el inicio: no es una solicitud
            para([ev["usuario_id"]], f"Ya puedes entrar a {proyecto}", "Tu solicitud fue aprobada.")

    elif tipo == "propuesta_pendiente":
        autor = ev.get("autor") or "Alguien"
        otros = [m["id"] for m in await _miembros(db, pid)
                 if _norm(m["nombre"]) != _norm(autor) and m["puede_aprobar"]]
        para(otros, f"La IA propone un cambio en {proyecto}",
             f"Pedido por {autor}: {_corto(ev.get('resumen'), 100)} — revísalo para aprobarlo o rechazarlo.")

    elif tipo == "propuesta_decidida":
        autor, por = ev.get("autor") or "", ev.get("por") or "Alguien"
        if autor and _norm(autor) != _norm(por):
            destinatarios = [m["id"] for m in await _miembros(db, pid) if _norm(m["nombre"]) == _norm(autor)]
            verbo = "aprobó" if ev.get("aprobada") else "rechazó"
            para(destinatarios, f"{por} {verbo} tu pedido a la IA", _corto(ev.get("resumen"), 120))

    elif tipo == "comentario":
        autor = ev.get("autor") or "Alguien"
        otros = [m["id"] for m in await _miembros(db, pid)
                 if m["id"] != ev.get("autor_id") and _norm(m["nombre"]) != _norm(autor)]
        para(otros, f"{autor} comentó en {proyecto}", _corto(ev.get("texto"), 120))

    return salida


# ─── Agrupar y guardar ──────────────────────────────────────────────────────

def _agrupar(notifs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Varias tareas para la misma persona en un mismo guardado → un solo aviso."""
    tareas: Dict[tuple, List[Dict[str, Any]]] = {}
    resto: List[Dict[str, Any]] = []
    for n in notifs:
        if n["tipo"] == "tarea_asignada":
            tareas.setdefault((n["usuario_id"], n["proyecto_id"]), []).append(n)
        else:
            resto.append(n)
    for grupo in tareas.values():
        if len(grupo) == 1:
            resto.append(grupo[0])
        else:
            primera = dict(grupo[0])
            primera["titulo"] = primera["titulo"].replace("Nueva tarea", f"{len(grupo)} tareas nuevas", 1)
            primera["mensaje"] = _corto(", ".join(g["mensaje"] for g in grupo[:3]) + ("…" if len(grupo) > 3 else ""), 160)
            resto.append(primera)
    return resto


async def _procesar_seguro(eventos: List[Dict[str, Any]]) -> None:
    try:
        await procesar(eventos)
    except Exception as e:   # nunca romper la operación original
        log.warning("[Notificaciones] No se pudieron generar: %s", e)


async def procesar(eventos: List[Dict[str, Any]], db=None) -> List[Dict[str, Any]]:
    """Genera y guarda las notificaciones. Usa su propia sesión salvo que se le pase una (tests)."""
    if db is None:
        from backend.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as propia:
            return await _procesar_en(propia, eventos)
    return await _procesar_en(db, eventos)


async def _procesar_en(db, eventos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from backend.modules.gestion_notificaciones.models import Notificacion

    notifs: List[Dict[str, Any]] = []
    for ev in eventos:
        notifs.extend(await _construir(db, ev))
    notifs = _agrupar(notifs)
    if not notifs:
        return []
    for n in notifs:
        db.add(Notificacion(**n))
    await db.commit()
    await enviar_push(db, notifs)
    return notifs


# ─── Firebase Cloud Messaging (opcional) ────────────────────────────────────

_firebase_app = None
_firebase_error: Optional[str] = None


def _ruta_credenciales() -> str:
    ruta = (settings.FIREBASE_CREDENTIALS or "").strip()
    if not ruta:
        return ""
    if not os.path.isabs(ruta):
        raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        candidatas = [os.path.join(raiz, ruta), os.path.join(raiz, "backend", ruta)]
        ruta = next((c for c in candidatas if os.path.isfile(c)), candidatas[0])
    return ruta


def firebase_app():
    """App de firebase-admin, o None si no hay credenciales (las notificaciones quedan solo en la app)."""
    global _firebase_app, _firebase_error
    if _firebase_app is not None or _firebase_error:
        return _firebase_app
    ruta = _ruta_credenciales()
    if not ruta or not os.path.isfile(ruta):
        _firebase_error = "sin credenciales"
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials
        _firebase_app = firebase_admin.initialize_app(credentials.Certificate(ruta), name="notificaciones")
    except Exception as e:
        _firebase_error = str(e)
        log.warning("[Notificaciones] Firebase no se pudo iniciar: %s", e)
    return _firebase_app


def config_web() -> Dict[str, Any]:
    """Lo que necesita el navegador para registrarse (son datos públicos de Firebase, no secretos)."""
    completo = all([settings.FIREBASE_WEB_API_KEY, settings.FIREBASE_PROJECT_ID, settings.FIREBASE_SENDER_ID,
                    settings.FIREBASE_APP_ID, settings.FIREBASE_VAPID_KEY])
    if not completo:
        return {"push": False}
    return {
        "push": True,
        "vapidKey": settings.FIREBASE_VAPID_KEY,
        "firebase": {
            "apiKey": settings.FIREBASE_WEB_API_KEY,
            "authDomain": f"{settings.FIREBASE_PROJECT_ID}.firebaseapp.com",
            "projectId": settings.FIREBASE_PROJECT_ID,
            "messagingSenderId": settings.FIREBASE_SENDER_ID,
            "appId": settings.FIREBASE_APP_ID,
        },
    }


async def enviar_push(db, notifs: List[Dict[str, Any]]) -> int:
    app = firebase_app()
    if app is None:
        return 0
    from firebase_admin import messaging

    usuarios = list({n["usuario_id"] for n in notifs})
    filas = (await db.execute(text(
        "SELECT usuario_id, token FROM dispositivos_push WHERE usuario_id = ANY(:u)"
    ), {"u": usuarios})).all()
    tokens: Dict[int, List[str]] = {}
    for uid, tok in filas:
        tokens.setdefault(uid, []).append(tok)

    base = settings.FRONTEND_URL.rstrip("/")
    invalidos: List[str] = []
    enviados = 0
    for n in notifs:
        lista = tokens.get(n["usuario_id"]) or []
        if not lista:
            continue
        mensaje = messaging.MulticastMessage(
            tokens=lista,
            notification=messaging.Notification(title=n["titulo"], body=n["mensaje"]),
            data={"tipo": n["tipo"], "url": n.get("url") or "/dashboard", "proyecto_id": str(n.get("proyecto_id") or "")},
            webpush=messaging.WebpushConfig(fcm_options=messaging.WebpushFCMOptions(link=f"{base}{n.get('url') or '/dashboard'}")),
        )
        try:
            r = await asyncio.to_thread(messaging.send_each_for_multicast, mensaje, False, app)
        except Exception as e:
            log.warning("[Notificaciones] Falló el envío push: %s", e)
            continue
        enviados += r.success_count
        for tok, resp in zip(lista, r.responses):
            if not resp.success and type(resp.exception).__name__ in ("UnregisteredError", "SenderIdMismatchError", "InvalidArgumentError"):
                invalidos.append(tok)
    if invalidos:
        await db.execute(text("DELETE FROM dispositivos_push WHERE token = ANY(:t)"), {"t": invalidos})
        await db.commit()
    return enviados
