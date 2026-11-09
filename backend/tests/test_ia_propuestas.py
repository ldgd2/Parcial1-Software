"""Flujo de la IA (simulada): pedido → propuesta pendiente → aprobar/rechazar → memoria y avisos."""
from sqlalchemy import text

from backend.modules.gestion_notificaciones.services.notificaciones_service import procesar

ESTADO_ANTES = {"nodes": [{"id": "n-venta", "nombre": "Venta", "atributos": [], "metodos": []}], "relations": []}


async def _pedir(cliente, equipo, usuario, prompt="agrega la clase Pago relacionada con Venta", **extra):
    r = await cliente.como(usuario).post("/prompt/generar", json={
        "prompt": prompt, "context": "Venta(+id:int)", "proyecto_id": equipo.pid,
        "provider": "kimi", "estado_antes": ESTADO_ANTES, **extra,
    })
    assert r.status_code == 200, r.text
    return r.json()


async def test_pedido_crea_propuesta_pendiente_con_autor(cliente, equipo, ia, eventos_notif, db):
    datos = await _pedir(cliente, equipo, equipo.ana)

    assert len(ia.prompts) == 1, "debe llamar a la IA exactamente una vez"
    assert {"Venta", "Pago"} <= {n.get("name") for n in datos["nodes"]}
    assert datos["version_id"], "la respuesta debe traer la versión del historial"

    v = (await cliente.get(f"/api/ia/contexto/{equipo.pid}/versiones/{datos['version_id']}")).json()
    assert v["estado_propuesta"] == "pendiente"
    assert v["autor"] == "Ana Test"
    assert v["estado_antes"] == ESTADO_ANTES
    assert {n.get("name") for n in v["propuesta"]["nodes"]} >= {"Pago"}

    # Aviso: la propuesta le llega al resto del equipo, no a quien la pidió
    assert [e["tipo"] for e in eventos_notif] == ["propuesta_pendiente"]
    notifs = await procesar(eventos_notif, db=db)
    assert [n["usuario_id"] for n in notifs] == [equipo.beto.id]
    assert "Ana Test" in notifs[0]["mensaje"]


async def test_aprobar_registra_quien_y_avisa_al_que_pidio(cliente, equipo, ia, eventos_notif, db):
    vid = (await _pedir(cliente, equipo, equipo.ana))["version_id"]
    eventos_notif.clear()

    r = await cliente.como(equipo.beto).post(f"/api/ia/contexto/{equipo.pid}/versiones/{vid}/decision",
                                              json={"aceptar": True, "estado_antes": ESTADO_ANTES})
    assert r.status_code == 200, r.text
    v = r.json()
    assert v["estado_propuesta"] == "aprobada"
    assert v["decidida_por"] == "Beto Test"
    assert v["decidida_en"]

    # Nadie puede volver a decidirla
    otra = await cliente.como(equipo.ana).post(f"/api/ia/contexto/{equipo.pid}/versiones/{vid}/decision", json={"aceptar": False})
    assert otra.status_code == 409
    assert "Beto Test" in otra.text

    # Aviso a Ana: "Beto aprobó tu pedido"
    decididas = [e for e in eventos_notif if e["tipo"] == "propuesta_decidida"]
    assert len(decididas) == 1
    notifs = await procesar(decididas, db=db)
    assert [n["usuario_id"] for n in notifs] == [equipo.ana.id]
    assert notifs[0]["titulo"] == "Beto Test aprobó tu pedido a la IA"

    # La memoria del proyecto recuerda lo aprobado
    memorias = (await cliente.get(f"/api/ia/contexto/{equipo.pid}/memorias")).json()
    assert memorias, "aprobar una propuesta debe dejar una memoria"


async def test_rechazar_no_se_aplica_y_queda_en_memoria(cliente, equipo, ia, db):
    vid = (await _pedir(cliente, equipo, equipo.ana))["version_id"]
    r = await cliente.como(equipo.ana).post(f"/api/ia/contexto/{equipo.pid}/versiones/{vid}/decision", json={"aceptar": False})
    assert r.status_code == 200
    assert r.json()["estado_propuesta"] == "rechazada"
    assert r.json()["decidida_por"] == "Ana Test"

    memorias = (await cliente.get(f"/api/ia/contexto/{equipo.pid}/memorias")).json()
    assert any(m["topic_key"].startswith("rechazos/") for m in memorias), memorias


async def test_decidir_version_que_no_es_propuesta_da_400(cliente, equipo):
    r = await cliente.como(equipo.ana).post(f"/api/ia/contexto/{equipo.pid}/versiones",
                                             json={"intent": "MANUAL", "cmd": "movió Venta", "delta": "~Venta", "autor": "Ana Test"})
    assert r.status_code == 201, r.text
    r2 = await cliente.post(f"/api/ia/contexto/{equipo.pid}/versiones/{r.json()['id']}/decision", json={"aceptar": True})
    assert r2.status_code == 400


async def test_la_ia_recibe_las_correcciones_abiertas(cliente, equipo, ia):
    await _pedir(cliente, equipo, equipo.ana, prompt="soluciona la corrección de Venta",
                 correcciones=[{"id": "c1", "target": "Venta", "text": "Falta la clave primaria idVenta", "estado": "abierta"}])
    contexto = ia.prompts[-1]["context"] or ""
    assert "Falta la clave primaria idVenta" in contexto


async def test_si_el_usuario_detiene_la_ia_no_se_registra_nada(equipo, ia, db):
    from backend.modules.gestion_asistencia_ia.generar_diagrama_prompt.services.prompt_service import generar_diagrama_desde_prompt

    async def detenido():
        return True

    resultado = await generar_diagrama_desde_prompt(prompt="agrega Pago", proyecto_id=equipo.pid, db=db, cancelado=detenido)
    assert resultado.get("nodes"), "la IA respondió"
    assert not resultado.get("version_id")
    n = (await db.execute(text("SELECT count(*) FROM versiones_contexto_ia WHERE proyecto_id = :p"), {"p": equipo.pid})).scalar()
    assert n == 0


async def test_historial_lista_y_filtra(cliente, equipo, ia):
    await _pedir(cliente, equipo, equipo.ana)
    await cliente.como(equipo.beto).post(f"/api/ia/contexto/{equipo.pid}/versiones",
                                          json={"intent": "MANUAL", "cmd": "editó a mano", "delta": "~Venta", "autor": "Beto Test"})
    pagina = (await cliente.get(f"/api/ia/contexto/{equipo.pid}/versiones")).json()
    intents = [v["intent"].upper() for v in pagina["items"]]
    assert "MANUAL" in intents and len(intents) == 2
