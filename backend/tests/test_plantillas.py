"""CU42: plantillas de proyecto."""

LIENZO = {
    "nodes": [{"id": "a", "nombre": "Cliente", "x": 0, "y": 0}, {"id": "b", "nombre": "Pedido", "x": 300, "y": 0}],
    "relations": [{"id": "r", "sourceId": "a", "targetId": "b", "type": "association"}],
}


async def test_plantillas_base_validas(cliente):
    lista = (await cliente.get("/api/plantillas")).json()
    base = [p for p in lista if p["origen"] == "base"]
    assert {p["id"] for p in base} == {"base:ventas", "base:universidad", "base:hospital", "base:biblioteca"}
    for meta in base:
        p = (await cliente.get(f"/api/plantillas/{meta['id']}")).json()
        ids = {n["id"] for n in p["lienzo"]["nodes"]}
        assert len(ids) == meta["clases"] > 0
        assert all(r["sourceId"] in ids and r["targetId"] in ids for r in p["lienzo"]["relations"]), meta["id"]
    assert (await cliente.get("/api/plantillas/base:no-existe")).status_code == 404


async def test_guardar_ver_y_borrar_plantilla_propia(cliente, equipo):
    r = await cliente.como(equipo.ana).post("/api/plantillas", json={"nombre": "Mi tienda", "descripcion": "", "lienzo": LIENZO})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    assert pid.startswith("u:") and r.json()["clases"] == 2

    assert pid in {p["id"] for p in (await cliente.como(equipo.ana).get("/api/plantillas")).json()}
    # Beto no la ve ni la puede abrir o borrar
    assert pid not in {p["id"] for p in (await cliente.como(equipo.beto).get("/api/plantillas")).json()}
    assert (await cliente.como(equipo.beto).get(f"/api/plantillas/{pid}")).status_code == 404
    assert (await cliente.como(equipo.beto).delete(f"/api/plantillas/{pid}")).status_code == 404

    assert (await cliente.como(equipo.ana).delete(f"/api/plantillas/{pid}")).status_code == 204
    assert (await cliente.como(equipo.ana).get(f"/api/plantillas/{pid}")).status_code == 404


async def test_plantilla_vacia_o_base_no_se_puede(cliente, equipo):
    vacia = await cliente.como(equipo.ana).post("/api/plantillas", json={"nombre": "x", "descripcion": "", "lienzo": {"nodes": []}})
    assert vacia.status_code == 400
    assert (await cliente.como(equipo.ana).delete("/api/plantillas/base:ventas")).status_code == 400
    sin_sesion = await cliente.como(None).post("/api/plantillas", json={"nombre": "x", "descripcion": "", "lienzo": LIENZO})
    assert sin_sesion.status_code == 401
