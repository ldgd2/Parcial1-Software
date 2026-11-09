"""CU40: quién cambió la pizarra (a mano, aprobando a la IA, resolviendo correcciones)."""
import json
import time

from backend.modules.gestion_asistencia_ia.gestionar_contexto_persistente.services.actividad_service import (
    _pedido_visible,
    contribucion,
)


def test_pedido_visible_quita_las_instrucciones_del_sistema():
    cmd = ("REFACTORIZACIÓN Y LIMPIEZA DE DIAGRAMA:\ncorrige el diagrama: agrega +id a Venta.\n\n"
           "DIRECTRICES ARQUITECTÓNICAS:\n- Normaliza todo")
    assert _pedido_visible(cmd) == "corrige el diagrama: agrega +id a Venta."
    assert _pedido_visible("agrega Pago") == "agrega Pago"
    assert _pedido_visible(None) == ""


async def test_actividad_atribuye_la_ia_a_quien_aprueba(cliente, equipo, ia, db):
    ahora_ms = int(time.time() * 1000)
    # Lienzo con una corrección señalada por Ana y resuelta por Beto
    equipo.proyecto.lienzo_json = json.dumps({
        "nodes": [{"id": "n-venta", "nombre": "Venta"}],
        "relations": [],
        "correcciones": {"n-venta": [{
            "id": "c1", "targetId": "n-venta", "texto": "Falta la PK", "autorNombre": "Ana Test",
            "fecha": ahora_ms - 60_000, "estado": "resuelta", "resueltoPorNombre": "Beto Test", "fechaResolucion": ahora_ms,
        }]},
    })
    await db.commit()

    # Beto edita a mano; Ana pide a la IA y Beto lo aprueba; Ana pide otra y la rechaza ella
    await cliente.como(equipo.beto).post(f"/api/ia/contexto/{equipo.pid}/versiones",
                                          json={"intent": "MANUAL", "cmd": "editó", "delta": "~Venta", "autor": "Beto Test"})
    for aceptar, decide in ((True, equipo.beto), (False, equipo.ana)):
        r = await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "agrega Pago", "proyecto_id": equipo.pid})
        vid = r.json()["version_id"]
        d = await cliente.como(decide).post(f"/api/ia/contexto/{equipo.pid}/versiones/{vid}/decision", json={"aceptar": aceptar})
        assert d.status_code == 200, d.text

    r = await cliente.get(f"/api/ia/contexto/{equipo.pid}/actividad?todo=true")
    assert r.status_code == 200
    datos = r.json()
    por = {m["nombre"]: m for m in datos["miembros"]}

    beto, ana = por["Beto Test"], por["Ana Test"]
    assert beto["cambios_manuales"] == 1
    assert beto["ia_aprobados"] == 1, "el cambio de la IA cuenta para quien lo aprobó"
    assert beto["correcciones_resueltas"] == 1
    assert beto["cambios_pizarra"] == 3
    assert ana["ia_aprobados"] == 0 and ana["ia_rechazados"] == 1
    assert ana["correcciones_senaladas"] == 1
    assert ana["cambios_pizarra"] == 0
    assert datos["miembros"][0]["nombre"] == "Beto Test", "ordenado por cambios en la pizarra"

    aprobada = next(e for e in datos["eventos"] if e["tipo"] == "ia_aprobada")
    assert aprobada["quien"] == "Beto Test" and aprobada["pedido_por"] == "Ana Test"
    assert aprobada["pedido"] == "agrega Pago"
    resuelta = next(e for e in datos["eventos"] if e["tipo"] == "correccion_resuelta")
    assert resuelta["clase"] == "Venta" and resuelta["senalada_por"] == "Ana Test"
    assert "pedidos_ia" not in datos["totales"], "ya no se cuentan los pedidos a la IA"


async def test_actividad_respeta_el_periodo(equipo, db):
    from sqlalchemy import text

    viejo = int(time.time()) - 40 * 86400
    await db.execute(text(
        "INSERT INTO versiones_contexto_ia (proyecto_id, ts, intent, cmd, resumen, delta, autor) "
        "VALUES (:p, :ts, 'MANUAL', '', '', '~Venta', 'Ana Test')"
    ), {"p": equipo.pid, "ts": viejo})
    await db.commit()
    assert (await contribucion(db, equipo.pid, 30))["miembros"] == []
    assert (await contribucion(db, equipo.pid, None))["miembros"][0]["cambios_manuales"] == 1


async def test_pendientes_se_avisan_sin_contar_para_nadie(cliente, equipo, ia):
    await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "agrega Pago", "proyecto_id": equipo.pid})
    datos = (await cliente.get(f"/api/ia/contexto/{equipo.pid}/actividad?todo=true")).json()
    assert datos["totales"]["ia_pendientes"] == 1
    assert all(m["cambios_pizarra"] == 0 for m in datos["miembros"])
    assert datos["eventos"][0]["tipo"] == "ia_pendiente"
