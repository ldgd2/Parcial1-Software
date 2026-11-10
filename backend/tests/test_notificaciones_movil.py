"""Push de la app móvil (rutas /api/notifications del líder) con Firebase SIMULADO."""
from sqlalchemy import text

from backend.modules.gestion_notificaciones.services import notifications_service

TOKEN = "fcm-movil-" + "y" * 40


async def _tokens(db):
    return (await db.execute(text("SELECT user_id FROM notifications WHERE device_token = :t"), {"t": TOKEN})).all()


async def test_registrar_celular_pide_sesion_y_es_de_la_cuenta_propia(cliente, equipo, db):
    cuerpo = {"user_id": equipo.beto.id, "device_token": TOKEN}
    assert (await cliente.como(None).post("/api/notifications/register", json=cuerpo)).status_code == 401
    assert (await cliente.como(equipo.ana).post("/api/notifications/register", json=cuerpo)).status_code == 403, \
        "no se puede registrar un celular a nombre de otro"
    assert await _tokens(db) == []

    assert (await cliente.como(equipo.beto).post("/api/notifications/register", json=cuerpo)).status_code == 201
    assert await _tokens(db) == [(equipo.beto.id,)]


async def test_celular_compartido_pasa_a_la_cuenta_actual(cliente, equipo, db):
    assert (await cliente.como(equipo.ana).post("/api/notifications/register", json={"device_token": TOKEN})).status_code == 201
    assert (await cliente.como(equipo.beto).post("/api/notifications/register", json={"device_token": TOKEN})).status_code == 201
    assert await _tokens(db) == [(equipo.beto.id,)], "sin error de duplicado y sin que Ana siga recibiendo"


async def test_enviar_push(cliente, equipo, db, monkeypatch):
    enviados = []
    monkeypatch.setattr(notifications_service, "send_fcm_message",
                        lambda token, title, body, data=None: enviados.append((token, title)) or "msg-123")
    yo = cliente.como(equipo.beto)
    cuerpo = {"user_id": equipo.beto.id, "title": "Hola", "body": "Prueba"}

    assert (await yo.post("/api/notifications/send", json=cuerpo)).status_code == 404, "sin celular registrado"
    await yo.post("/api/notifications/register", json={"device_token": TOKEN})

    r = await yo.post("/api/notifications/send", json=cuerpo)
    assert r.status_code == 201, r.text
    assert r.json()["message_id"] == "msg-123"
    assert enviados == [(TOKEN, "Hola")]
    n = (await db.execute(text(
        "SELECT count(*) FROM notifications_log l JOIN notifications t ON t.id = l.notification_id WHERE t.user_id = :u"
    ), {"u": equipo.beto.id})).scalar()
    assert n == 1, "queda en la bitácora"

    assert (await yo.post("/api/notifications/send", json={**cuerpo, "user_id": equipo.ana.id})).status_code == 403


async def test_enviar_sin_firebase_da_503(cliente, equipo, monkeypatch):
    def sin_firebase(*a, **k):
        raise RuntimeError("Firebase Admin no esta configurado.")

    monkeypatch.setattr(notifications_service, "send_fcm_message", sin_firebase)
    yo = cliente.como(equipo.beto)
    await yo.post("/api/notifications/register", json={"device_token": TOKEN})
    r = await yo.post("/api/notifications/send", json={"user_id": equipo.beto.id, "title": "x", "body": "y"})
    assert r.status_code == 503
