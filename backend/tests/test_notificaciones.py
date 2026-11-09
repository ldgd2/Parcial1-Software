"""CU39: qué genera avisos, a quién le llegan y la API de la campana."""
from backend.modules.gestion_modelado.models import ComentarioElemento
from backend.modules.gestion_notificaciones.models import Notificacion
from backend.modules.gestion_notificaciones.services import notificaciones_service
from backend.modules.gestion_notificaciones.services.notificaciones_service import procesar
from backend.modules.gestion_proyectos.models import ColaboradorProyecto, Proyecto
from backend.modules.gestion_usuarios.models import TareaIA, UsuarioRegistrado


async def test_varias_tareas_un_solo_aviso(equipo, eventos_notif, db):
    db.add_all([TareaIA(proyecto_id=equipo.pid, usuario_id=equipo.beto.id, titulo=t) for t in ("Modelar Cliente", "Modelar Venta")])
    await db.commit()
    assert [e["tipo"] for e in eventos_notif] == ["tarea_asignada", "tarea_asignada"]
    notifs = await procesar(eventos_notif, db=db)
    assert len(notifs) == 1
    assert notifs[0]["usuario_id"] == equipo.beto.id
    assert notifs[0]["titulo"].startswith("2 tareas nuevas")
    assert "Modelar Cliente" in notifs[0]["mensaje"]


async def test_si_se_deshace_no_se_avisa(equipo, eventos_notif, db):
    db.add(TareaIA(proyecto_id=equipo.pid, usuario_id=equipo.beto.id, titulo="no va"))
    await db.flush()
    await db.rollback()
    assert eventos_notif == []


async def test_comentarios_avisan_al_resto_pero_no_los_de_la_ia(equipo, eventos_notif, db):
    db.add(ComentarioElemento(id="t-c1", proyecto_id=equipo.pid, elemento_id="n1", autor_id=equipo.beto.id,
                              autor_nombre="Beto Test", texto="Falta la PK"))
    db.add(ComentarioElemento(id="t-c2", proyecto_id=equipo.pid, elemento_id="n1", autor_nombre="IA (aprobado por Ana Test)", texto="x"))
    await db.commit()
    assert len(eventos_notif) == 1
    notifs = await procesar(eventos_notif, db=db)
    assert [n["usuario_id"] for n in notifs] == [equipo.ana.id]
    assert notifs[0]["titulo"].startswith("Beto Test comentó")


async def test_solicitud_para_unirse_y_aprobacion(equipo, eventos_notif, db):
    caro = UsuarioRegistrado(nombre="Caro Test", email=f"caro_{equipo.pid}@test.local")
    db.add(caro)
    await db.flush()
    c = ColaboradorProyecto(proyecto_id=equipo.pid, usuario_id=caro.id, rol_proyecto="invitado", estado="pendiente")
    db.add(c)
    await db.commit()
    c.estado = "aprobado"
    await db.commit()

    notifs = await procesar(eventos_notif, db=db)
    por_tipo = {n["tipo"]: n for n in notifs}
    assert por_tipo["solicitud_union"]["usuario_id"] == equipo.ana.id, "solo al anfitrión"
    assert por_tipo["solicitud_aprobada"]["usuario_id"] == caro.id
    assert len(notifs) == 2


async def test_crear_proyecto_no_avisa(eventos_notif, db):
    yo = UsuarioRegistrado(nombre="Solo Test", email="solo_np@test.local")
    db.add(yo)
    await db.flush()
    p = Proyecto(nombre="Nuevo")
    db.add(p)
    await db.flush()
    db.add(ColaboradorProyecto(proyecto_id=p.id, usuario_id=yo.id, rol_proyecto="anfitrion", estado="aprobado"))
    await db.commit()
    assert await procesar(eventos_notif, db=db) == []


async def test_api_campana(cliente, equipo, db):
    for t in ("uno", "dos"):
        db.add(Notificacion(usuario_id=equipo.beto.id, proyecto_id=equipo.pid, tipo="comentario", titulo=t, url="/diagrama/1"))
    ajena = Notificacion(usuario_id=equipo.ana.id, tipo="comentario", titulo="de Ana")
    db.add(ajena)
    await db.commit()

    yo = cliente.como(equipo.beto)
    r = (await yo.get("/api/notificaciones")).json()
    assert r["no_leidas"] == 2 and [n["titulo"] for n in r["items"]] == ["dos", "uno"]

    assert (await yo.post(f"/api/notificaciones/{r['items'][0]['id']}/leer")).status_code == 200
    assert (await yo.get("/api/notificaciones")).json()["no_leidas"] == 1
    assert (await yo.post(f"/api/notificaciones/{ajena.id}/leer")).status_code == 404, "no se tocan avisos ajenos"
    assert (await yo.post("/api/notificaciones/leer-todas")).json()["marcadas"] == 1
    assert (await yo.get("/api/notificaciones")).json()["no_leidas"] == 0
    assert (await cliente.como(None).get("/api/notificaciones")).status_code == 401


async def test_dispositivo_push_pasa_a_la_cuenta_actual(cliente, equipo, db):
    from sqlalchemy import text

    token = "token-de-prueba-" + "x" * 30
    assert (await cliente.como(equipo.ana).post("/api/notificaciones/dispositivos", json={"token": token})).status_code == 200
    assert (await cliente.como(equipo.beto).post("/api/notificaciones/dispositivos", json={"token": token})).status_code == 200
    filas = (await db.execute(text("SELECT usuario_id FROM dispositivos_push WHERE token = :t"), {"t": token})).all()
    assert filas == [(equipo.beto.id,)]
    assert (await cliente.como(equipo.beto).delete(f"/api/notificaciones/dispositivos?token={token}")).status_code == 200
    assert (await db.execute(text("SELECT count(*) FROM dispositivos_push WHERE token = :t"), {"t": token})).scalar() == 0


async def test_config_push_sin_firebase(cliente, monkeypatch):
    monkeypatch.setattr(notificaciones_service.settings, "FIREBASE_VAPID_KEY", "")
    assert (await cliente.get("/api/notificaciones/config")).json() == {"push": False}
