"""Pedir acceso a una sala y que el anfitrión apruebe o rechace (usuarios con cuenta)."""
from sqlalchemy import text

from backend.modules.gestion_usuarios.models import UsuarioRegistrado


async def _caro(db, equipo):
    caro = UsuarioRegistrado(nombre="Caro Test", email=f"caro_u_{equipo.pid}@test.local")
    db.add(caro)
    await db.commit()
    return caro


async def _estado(db, pid, uid):
    return (await db.execute(text("SELECT estado FROM colaboradores_proyecto WHERE proyecto_id=:p AND usuario_id=:u"),
                             {"p": pid, "u": uid})).scalar()


def _como(cliente, db, usuario):
    """En el servidor cada pedido abre su propia sesión; aquí todos comparten una, así que se
    descarta lo que tiene en memoria para que cada pedido lea la base como un pedido real."""
    from backend.modules.gestion_proyectos.models import Proyecto

    for obj in list(db.identity_map.values()):
        if isinstance(obj, Proyecto):
            db.expire(obj, ["colaboradores"])   # solo la lista de colaboradores; el resto sigue cargado
    return cliente.como(usuario)


async def test_rechazar_se_mantiene_aunque_la_espera_siga_abierta(cliente, equipo, db, eventos_notif):
    caro = await _caro(db, equipo)
    pid, codigo, ana, caro_id = equipo.pid, equipo.proyecto.codigo_acceso, equipo.ana, caro.id

    r = await _como(cliente, db, caro).get(f"/salas/unirse/{codigo}")
    assert r.json()["acceso"] == "pendiente"
    avisos = [e["tipo"] for e in eventos_notif].count("solicitud_union")

    r = await _como(cliente, db, ana).post(f"/proyectos/{pid}/solicitudes/{caro_id}", json={"aprobar": False})
    assert r.status_code == 200, r.text
    assert await _estado(db, pid, caro_id) == "rechazado"

    # La pantalla de espera vuelve a consultar cada 3 s: antes eso creaba otra solicitud pendiente
    for _ in range(3):
        r = await _como(cliente, db, caro).get(f"/salas/unirse/{codigo}")
        assert r.status_code == 200 and r.json()["acceso"] == "rechazado"
    assert await _estado(db, pid, caro_id) == "rechazado"
    assert [e["tipo"] for e in eventos_notif].count("solicitud_union") == avisos, "al anfitrión no le llegan avisos repetidos"
    assert (await _como(cliente, db, ana).get(f"/proyectos/{pid}/solicitudes")).json() == []

    # y no entra al proyecto
    assert (await _como(cliente, db, caro).get(f"/api/proyectos/{pid}/miembros")).status_code == 403


async def test_aprobar_da_acceso(cliente, equipo, db):
    caro = await _caro(db, equipo)
    pid, codigo, ana, caro_id = equipo.pid, equipo.proyecto.codigo_acceso, equipo.ana, caro.id
    await _como(cliente, db, caro).get(f"/salas/unirse/{codigo}")
    r = await _como(cliente, db, ana).post(f"/proyectos/{pid}/solicitudes/{caro_id}", json={"aprobar": True})
    assert r.status_code == 200
    assert (await _como(cliente, db, caro).get(f"/salas/unirse/{codigo}")).json()["acceso"] == "aprobado"
    assert (await _como(cliente, db, caro).get(f"/api/proyectos/{pid}/miembros")).status_code == 200


async def test_el_anfitrion_puede_volver_a_permitir_un_rechazo(cliente, equipo, db, eventos_notif):
    caro = await _caro(db, equipo)
    pid, codigo, ana, caro_id = equipo.pid, equipo.proyecto.codigo_acceso, equipo.ana, caro.id
    await _como(cliente, db, caro).get(f"/salas/unirse/{codigo}")
    await _como(cliente, db, ana).post(f"/proyectos/{pid}/solicitudes/{caro_id}", json={"aprobar": False})

    r = await _como(cliente, db, ana).get(f"/api/proyectos/{pid}/rechazados")
    assert [x["usuario_id"] for x in r.json()] == [caro_id]
    assert (await _como(cliente, db, equipo.beto).get(f"/api/proyectos/{pid}/rechazados")).status_code == 403, \
        "solo el anfitrión ve y decide los rechazos"
    assert (await _como(cliente, db, equipo.beto).post(f"/api/proyectos/{pid}/rechazados/{caro_id}/permitir")).status_code == 403

    eventos_notif.clear()
    r = await _como(cliente, db, ana).post(f"/api/proyectos/{pid}/rechazados/{caro_id}/permitir")
    assert r.status_code == 200, r.text
    assert await _estado(db, pid, caro_id) == "aprobado"
    assert [e["tipo"] for e in eventos_notif] == ["solicitud_aprobada"], "le llega el aviso de que ya puede entrar"
    assert (await _como(cliente, db, caro).get(f"/salas/unirse/{codigo}")).json()["acceso"] == "aprobado"
    assert (await _como(cliente, db, ana).get(f"/api/proyectos/{pid}/rechazados")).json() == []

    # no sirve para quien no fue rechazado
    assert (await _como(cliente, db, ana).post(f"/api/proyectos/{pid}/rechazados/{equipo.lucia.id}/permitir")).status_code == 404
