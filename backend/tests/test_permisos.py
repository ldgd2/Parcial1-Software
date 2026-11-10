"""CU38 (permisos persistentes) y CU43 (permisos validados en el backend)."""
import json

from sqlalchemy import text

from backend.modules.gestion_modelado.models import ComentarioElemento
from backend.modules.gestion_proyectos.models import ColaboradorProyecto
from backend.modules.gestion_usuarios.models import TareaIA, UsuarioRegistrado

ESTADO = {"nodes": [{"id": "n1", "nombre": "Venta"}], "relations": []}


async def _propuesta(cliente, equipo, ia):
    r = await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "agrega Pago", "proyecto_id": equipo.pid})
    assert r.status_code == 200, r.text
    return r.json()["version_id"]


async def _de_afuera(db):
    caro = UsuarioRegistrado(nombre="Caro Externa", email="caro_ext@test.local")
    db.add(caro)
    await db.flush()
    return caro


# ─── CU43: sin sesión → 401 ─────────────────────────────────────────────────

async def test_sin_sesion_no_se_puede_nada_del_proyecto(cliente, equipo, ia):
    vid = await _propuesta(cliente, equipo, ia)
    anonimo = cliente.como(None)
    for metodo, url, cuerpo in (
        ("get", f"/api/ia/contexto/{equipo.pid}/versiones", None),
        ("get", f"/api/ia/contexto/{equipo.pid}/actividad", None),
        ("post", f"/api/ia/contexto/{equipo.pid}/versiones/{vid}/decision", {"aceptar": True, "autor": "Alguien"}),
        ("post", "/prompt/generar", {"prompt": "agrega Pago", "proyecto_id": equipo.pid}),
        ("post", "/prompt/generar", {"prompt": "agrega Pago"}),
        ("get", f"/salas/{equipo.pid}/lienzo", None),
        ("get", f"/api/proyectos/{equipo.pid}/miembros", None),
        ("get", "/proyectos/todos", None),
    ):
        r = await (anonimo.get(url) if metodo == "get" else anonimo.post(url, json=cuerpo))
        assert r.status_code == 401, (url, r.status_code, r.text)


# ─── CU43: alguien de afuera → 403; proyecto inexistente → 404 ──────────────

async def test_quien_no_es_miembro_no_ve_el_proyecto(cliente, equipo, db):
    caro = await _de_afuera(db)
    ext = cliente.como(caro)
    assert (await ext.get(f"/api/ia/contexto/{equipo.pid}/versiones")).status_code == 403
    assert (await ext.get(f"/salas/{equipo.pid}/lienzo")).status_code == 403, "antes cargaba cualquier lienzo"
    assert (await ext.get(f"/api/modelado/comentarios/proyecto/{equipo.pid}")).status_code == 403
    assert (await ext.get("/api/ia/contexto/999999999/versiones")).status_code == 404


async def test_todos_los_proyectos_solo_para_admin(cliente, equipo):
    lista = (await cliente.como(equipo.beto).get("/proyectos/todos")).json()
    assert [p["id"] for p in lista] == [equipo.pid], "un usuario normal ve solo los suyos"


# ─── CU43: el lector ve y comenta, pero no cambia nada ──────────────────────

async def test_lector_ve_pero_no_cambia(cliente, equipo, ia, db):
    vid = await _propuesta(cliente, equipo, ia)
    lector = cliente.como(equipo.lucia)

    # Puede ver
    assert (await lector.get(f"/api/ia/contexto/{equipo.pid}/versiones")).status_code == 200
    assert (await lector.get(f"/api/ia/contexto/{equipo.pid}/actividad")).status_code == 200
    lienzo = await lector.get(f"/salas/{equipo.pid}/lienzo")
    assert lienzo.status_code == 200 and lienzo.json()["permiso"] == "lector"

    # No puede cambiar
    for metodo, url, cuerpo in (
        ("post", f"/api/ia/contexto/{equipo.pid}/versiones/{vid}/decision", {"aceptar": True}),
        ("post", f"/api/ia/contexto/{equipo.pid}/versiones", {"intent": "MANUAL", "cmd": "x"}),
        ("post", "/prompt/generar", {"prompt": "agrega Pago", "proyecto_id": equipo.pid}),
        ("put", f"/salas/{equipo.pid}/lienzo", {"lienzo": ESTADO}),
        ("post", f"/api/ia/contexto/{equipo.pid}/memorias", {"texto": "usar UUID"}),
        ("post", "/api/ia/tareas/crear", {"proyecto_id": equipo.pid, "usuario_id": equipo.lucia.id, "titulo": "x"}),
    ):
        r = await (lector.post(url, json=cuerpo) if metodo == "post" else lector.put(url, json=cuerpo))
        assert r.status_code == 403, (url, r.status_code, r.text)
        assert "solo lectura" in r.json()["detail"]

    # La propuesta sigue pendiente
    v = (await lector.get(f"/api/ia/contexto/{equipo.pid}/versiones/{vid}")).json()
    assert v["estado_propuesta"] == "pendiente"


async def test_lector_comenta_y_solo_toca_sus_comentarios(cliente, equipo, db):
    lector = cliente.como(equipo.lucia)
    r = await lector.post("/api/modelado/comentarios", json={"proyecto_id": equipo.pid, "elemento_id": "n1", "texto": "¿Falta la PK?"})
    assert r.status_code == 200, r.text
    mio = r.json()["id"]
    assert (await lector.delete(f"/api/modelado/comentarios/{mio}")).status_code == 200

    db.add(ComentarioElemento(id="t-ajeno", proyecto_id=equipo.pid, elemento_id="n1", autor_id=equipo.beto.id,
                              autor_nombre="Beto Test", texto="de Beto"))
    await db.commit()
    assert (await lector.delete("/api/modelado/comentarios/t-ajeno")).status_code == 403
    assert (await cliente.como(equipo.ana).delete("/api/modelado/comentarios/t-ajeno")).status_code == 200, "un editor sí"


async def test_lector_marca_solo_sus_tareas(cliente, equipo, db):
    suya = TareaIA(proyecto_id=equipo.pid, usuario_id=equipo.lucia.id, titulo="Revisar Venta")
    ajena = TareaIA(proyecto_id=equipo.pid, usuario_id=equipo.beto.id, titulo="API de pagos")
    db.add_all([suya, ajena])
    await db.commit()
    lector = cliente.como(equipo.lucia)
    r1 = await lector._req("PATCH", f"/api/ia/tareas/{suya.id}/completar?completada=true")
    r2 = await lector._req("PATCH", f"/api/ia/tareas/{ajena.id}/completar?completada=true")
    assert r1.status_code == 200, r1.text
    assert r2.status_code == 403


# ─── CU43: la autoría la da la sesión, no el cliente ────────────────────────

async def test_quien_aprueba_sale_de_la_sesion(cliente, equipo, ia):
    vid = await _propuesta(cliente, equipo, ia)
    r = await cliente.como(equipo.beto).post(f"/api/ia/contexto/{equipo.pid}/versiones/{vid}/decision",
                                              json={"aceptar": True, "autor": "Alguien Inventado"})
    assert r.json()["decidida_por"] == "Beto Test"
    v = await cliente.como(equipo.beto).post(f"/api/ia/contexto/{equipo.pid}/versiones",
                                              json={"intent": "MANUAL", "cmd": "movió Venta", "autor": "Otro"})
    assert v.json()["autor"] == "Beto Test"
    r = await cliente.como(equipo.beto).post("/prompt/generar", json={"prompt": "agrega Envio", "proyecto_id": equipo.pid, "autor": "Otro"})
    d = (await cliente.get(f"/api/ia/contexto/{equipo.pid}/versiones/{r.json()['version_id']}")).json()
    assert d["autor"] == "Beto Test"


# ─── CU38: permisos guardados ───────────────────────────────────────────────

async def test_anfitrion_cambia_el_permiso_y_queda_guardado(cliente, equipo, db):
    anfitrion = cliente.como(equipo.ana)
    miembros = {m["nombre"]: m for m in (await anfitrion.get(f"/api/proyectos/{equipo.pid}/miembros")).json()}
    assert miembros["Ana Test"]["nivel"] == "anfitrion"
    assert miembros["Beto Test"]["nivel"] == "editor"
    assert miembros["Lucia Test"]["nivel"] == "lector"

    r = await anfitrion.put(f"/api/proyectos/{equipo.pid}/miembros/{equipo.lucia.id}/permiso", json={"permiso": "edit"})
    assert r.status_code == 200 and r.json()["nivel"] == "editor"
    guardado = (await db.execute(text("SELECT permiso FROM colaboradores_proyecto WHERE proyecto_id=:p AND usuario_id=:u"),
                                 {"p": equipo.pid, "u": equipo.lucia.id})).scalar()
    assert guardado == "edit"
    # Ahora Lucía puede cambiar el diagrama
    ok = await cliente.como(equipo.lucia).post(f"/api/ia/contexto/{equipo.pid}/versiones", json={"intent": "MANUAL", "cmd": "x"})
    assert ok.status_code == 201
    assert (await cliente.como(equipo.lucia).get(f"/api/proyectos/{equipo.pid}/mi-permiso")).json() == {"nivel": "editor"}


async def test_solo_el_anfitrion_cambia_permisos(cliente, equipo):
    r = await cliente.como(equipo.beto).put(f"/api/proyectos/{equipo.pid}/miembros/{equipo.lucia.id}/permiso", json={"permiso": "edit"})
    assert r.status_code == 403 and "anfitrión" in r.json()["detail"]
    r = await cliente.como(equipo.ana).put(f"/api/proyectos/{equipo.pid}/miembros/{equipo.ana.id}/permiso", json={"permiso": "view"})
    assert r.status_code == 400, "el anfitrión no se puede quitar la edición"
    r = await cliente.como(equipo.ana).put(f"/api/proyectos/{equipo.pid}/miembros/{equipo.beto.id}/permiso", json={"permiso": "admin"})
    assert r.status_code == 422


async def test_el_cambio_llega_en_vivo_a_la_sala(cliente, equipo, monkeypatch):
    from backend.core.websockets.connection_manager import manager

    class WSFalso:
        def __init__(self):
            self.mensajes = []

        async def send_json(self, m):
            self.mensajes.append(m)

    lucia_ws, host_ws = WSFalso(), WSFalso()
    codigo = equipo.proyecto.codigo_acceso
    manager._init_sala(codigo)
    sala = manager.salas[codigo]
    sala["host"] = host_ws
    sala["guests"][f"auth_{equipo.lucia.id}"] = lucia_ws
    sala["readonly_guests"].add(f"auth_{equipo.lucia.id}")
    try:
        await cliente.como(equipo.ana).put(f"/api/proyectos/{equipo.pid}/miembros/{equipo.lucia.id}/permiso", json={"permiso": "edit"})
        assert f"auth_{equipo.lucia.id}" not in sala["readonly_guests"]
        assert lucia_ws.mensajes == [{"type": "role_changed", "role": "edit"}]
        assert host_ws.mensajes == [{"type": "role_updated", "guest_id": f"auth_{equipo.lucia.id}", "role": "edit"}]
    finally:
        manager.salas.pop(codigo, None)


async def test_websocket_lee_y_guarda_el_permiso(equipo, db):
    from backend.modules.gestion_proyectos.permisos_proyecto.permisos_service import guardar_desde_sala, permiso_guardado

    codigo = equipo.proyecto.codigo_acceso
    assert (await permiso_guardado(db, codigo, f"auth_{equipo.lucia.id}"))["permiso"] == "view"
    assert await permiso_guardado(db, codigo, "guest_123") is None, "invitados sin cuenta: no hay nada guardado"
    # El anfitrión la cambia desde la sala (mensaje change_role del WebSocket)
    assert await guardar_desde_sala(db, codigo, f"auth_{equipo.lucia.id}", "edit")
    assert (await permiso_guardado(db, codigo, f"auth_{equipo.lucia.id}"))["permiso"] == "edit"
    assert not await guardar_desde_sala(db, codigo, f"auth_{equipo.ana.id}", "view"), "al anfitrión no se le cambia"


async def test_lectores_no_reciben_aviso_de_aprobar(equipo, ia, cliente, eventos_notif, db):
    from backend.modules.gestion_notificaciones.services.notificaciones_service import procesar

    await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "agrega Pago", "proyecto_id": equipo.pid})
    notifs = await procesar([e for e in eventos_notif if e["tipo"] == "propuesta_pendiente"], db=db)
    assert [n["usuario_id"] for n in notifs] == [equipo.beto.id], "Lucía es lectora: no puede aprobar"
