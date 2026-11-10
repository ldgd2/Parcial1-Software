"""CU sin tests hasta ahora: repartir roles (IA simulada), detectar/corregir errores, seeders,
generar app móvil y refinar vista (IA simulada). Ningún test llama a un proveedor real."""
import io
import json
import zipfile

from sqlalchemy import text

from backend.modules.gestion_proyectos.models import ColaboradorProyecto
from backend.modules.gestion_usuarios.models import UsuarioRegistrado


def _attr(nombre, tipo="string", vis="+"):
    return {"id": f"a-{nombre}", "visibilidad": vis, "nombre": nombre, "tipo": tipo, "version": 0}


# Diagrama con el formato real del lienzo: Cliente 1-* Venta (FK cliente_id)
LIENZO = {
    "nodes": [
        {"id": "n-cli", "type": "class", "nombre": "Cliente",
         "atributos": [_attr("id", "int", "PK"), _attr("nombre"), _attr("email")], "metodos": []},
        {"id": "n-ven", "type": "class", "nombre": "Venta",
         "atributos": [_attr("id", "int", "PK"), _attr("total", "float"), _attr("cliente_id", "int", "FK")], "metodos": []},
    ],
    "relations": [{"id": "r1", "type": "association", "sourceId": "n-ven", "targetId": "n-cli", "label": ""}],
}


async def _con_lienzo(equipo, db, lienzo=LIENZO):
    equipo.proyecto.lienzo_json = json.dumps(lienzo)
    await db.commit()


# ─── Repartir roles (IA simulada) ───────────────────────────────────────────

def _ia_roles(monkeypatch, asignaciones, capturados=None):
    from backend.modules.gestion_asistencia_ia.repartir_roles.services import roles_service

    async def falsa(prompt, provider=None, api_key=None):
        if capturados is not None:
            capturados.append(prompt)
        return {"resumen": "Roles repartidos", "asignaciones": asignaciones}

    monkeypatch.setattr(roles_service, "_consultar_ia_roles", falsa)


async def _pendiente(equipo, db):
    caro = UsuarioRegistrado(nombre="Caro Pendiente", email=f"caro_{equipo.pid}@test.local")
    db.add(caro)
    await db.flush()
    db.add(ColaboradorProyecto(proyecto_id=equipo.pid, usuario_id=caro.id, rol_proyecto="invitado", estado="pendiente"))
    await db.commit()
    return caro


async def test_repartir_roles_propone_y_luego_guarda(cliente, equipo, db, monkeypatch):
    await _con_lienzo(equipo, db)
    caro = await _pendiente(equipo, db)
    prompts = []
    _ia_roles(monkeypatch, [
        {"usuario_id": equipo.ana.id, "rol_ia": "Líder Backend", "areas": ["backend"], "clases": ["Venta"]},
        {"usuario_id": equipo.beto.id, "rol_ia": "Frontend", "areas": ["frontend"], "clases": ["Cliente"]},
    ], prompts)
    yo = cliente.como(equipo.ana)

    r = await yo.post("/api/ia/roles/repartir", json={"proyecto_id": equipo.pid, "persistir": False})
    assert r.status_code == 200, r.text
    assert {x["rol_ia"] for x in r.json()["roles"]} == {"Líder Backend", "Frontend"}
    assert "Caro Pendiente" not in prompts[0], "quien no fue aprobado no entra al reparto"
    assert "Cliente" in prompts[0] and "Venta" in prompts[0], "la IA recibe las clases del diagrama"
    sin_guardar = (await db.execute(text("SELECT count(*) FROM colaboradores_proyecto WHERE proyecto_id=:p AND rol_ia IS NOT NULL"),
                                    {"p": equipo.pid})).scalar()
    assert sin_guardar == 0, "con persistir=False solo se propone"

    r = await yo.post("/api/ia/roles/repartir", json={"proyecto_id": equipo.pid, "persistir": True})
    assert r.status_code == 200, r.text
    filas = dict((await db.execute(text("SELECT usuario_id, rol_ia FROM colaboradores_proyecto WHERE proyecto_id=:p"),
                                   {"p": equipo.pid})).all())
    assert filas[equipo.ana.id] == "Líder Backend" and filas[equipo.beto.id] == "Frontend"
    assert filas[caro.id] is None
    lienzo = json.loads((await db.execute(text("SELECT lienzo_json FROM proyectos WHERE id=:p"), {"p": equipo.pid})).scalar())
    assert {n["nombre"]: n.get("responsable") for n in lienzo["nodes"]} == {"Cliente": "Beto Test", "Venta": "Ana Test"}


async def test_repartir_roles_permisos(cliente, equipo, monkeypatch):
    _ia_roles(monkeypatch, [])
    r = await cliente.como(equipo.lucia).post("/api/ia/roles/repartir", json={"proyecto_id": equipo.pid})
    assert r.status_code == 403, "una lectora no reparte roles"
    assert (await cliente.como(equipo.lucia).get(f"/api/ia/roles/proyecto/{equipo.pid}")).status_code == 200


async def test_asignar_rol_no_mete_gente_al_proyecto(cliente, equipo, db):
    ajeno = UsuarioRegistrado(nombre="Ajeno", email=f"ajeno_{equipo.pid}@test.local")
    db.add(ajeno)
    await db.commit()
    yo = cliente.como(equipo.ana)
    cuerpo = {"proyecto_id": equipo.pid, "usuario_id": ajeno.id, "rol_ia": "QA", "areas": ["testing"]}

    assert (await yo.put("/api/ia/roles/asignar", json=cuerpo)).status_code == 404
    n = (await db.execute(text("SELECT count(*) FROM colaboradores_proyecto WHERE proyecto_id=:p AND usuario_id=:u"),
                          {"p": equipo.pid, "u": ajeno.id})).scalar()
    assert n == 0, "antes quedaba como miembro aprobado (editor) sin que el anfitrión lo aceptara"

    r = await yo.put("/api/ia/roles/asignar", json={**cuerpo, "usuario_id": equipo.beto.id})
    assert r.status_code == 200 and r.json()["rol_ia"] == "QA"


async def test_repartir_tareas_solo_a_miembros_aprobados(cliente, equipo, db, monkeypatch):
    from backend.modules.gestion_asistencia_ia.repartir_tareas.services import tareas_service

    caro = await _pendiente(equipo, db)
    ajeno = UsuarioRegistrado(nombre="Ajeno", email=f"ajeno2_{equipo.pid}@test.local")
    db.add(ajeno)
    await db.commit()

    async def ia(prompt, provider=None, api_key=None):
        assert "Caro Pendiente" not in prompt
        return {"tareas": [
            {"usuario_id": caro.id, "tipo": "diagrama", "titulo": "Para la pendiente"},
            {"usuario_id": ajeno.id, "tipo": "diagrama", "titulo": "Para el ajeno"},
        ]}

    monkeypatch.setattr(tareas_service, "_llamar_ia_tareas", ia)
    r = await cliente.como(equipo.ana).post("/api/ia/tareas/repartir", json={
        "proyecto_id": equipo.pid, "persistir": True,
        "colaboradores": [{"usuario_id": ajeno.id, "nombre": "Ajeno"}],
    })
    assert r.status_code == 200, r.text
    dueños = {u for (u,) in (await db.execute(text("SELECT usuario_id FROM tareas_ia WHERE proyecto_id=:p"),
                                              {"p": equipo.pid})).all()}
    assert caro.id not in dueños and ajeno.id not in dueños
    assert dueños <= {equipo.ana.id, equipo.beto.id, equipo.lucia.id}


# ─── Detectar / corregir errores del diseño (sin IA) ────────────────────────

MALO = {
    "nodes": [
        {"id": "n1", "type": "class", "nombre": "Producto", "atributos": [_attr("nombre"), _attr("precio", "float")]},
        {"id": "n2", "type": "class", "nombre": "Categoria", "atributos": [_attr("id", "int", "PK"), _attr("nombre")]},
    ],
    "relations": [{"id": "r1", "type": "association", "sourceId": "n1", "targetId": "n2"}],
}


async def test_detectar_y_corregir_tabla_sin_pk(cliente, equipo):
    yo = cliente.como(equipo.beto)
    r = await yo.post("/api/interoperabilidad/detectar-errores", json=MALO)
    assert r.status_code == 200, r.text
    rep = r.json()
    assert not rep["es_valido"]
    assert any(e["tipo"] == "sin_pk" and e["tabla"] == "Producto" for e in rep["errores"])

    r = await yo.post("/api/interoperabilidad/corregir-errores", json=MALO)
    assert r.status_code == 200, r.text
    corregido = r.json()
    assert corregido["errores_corregidos"] >= 1
    r = await yo.post("/api/interoperabilidad/detectar-errores",
                      json={"nodes": corregido["fixed_nodes"], "relations": corregido["fixed_relations"]})
    assert not any(e["tipo"] == "sin_pk" for e in r.json()["errores"]), "después de corregir ya no falta la PK"

    assert (await cliente.como(None).post("/api/interoperabilidad/detectar-errores", json=MALO)).status_code == 401


# ─── Seeders (sin IA) ───────────────────────────────────────────────────────

async def test_seeders_respetan_el_orden_de_las_fk(cliente, equipo, db):
    await _con_lienzo(equipo, db)
    r = await cliente.como(equipo.lucia).post("/api/ia/seeders/generar",
                                              json={"proyecto_id": equipo.pid, "cantidad_por_tabla": 3})
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["orden_insercion"].index("Cliente") < s["orden_insercion"].index("Venta"), "primero la tabla referenciada"
    assert s["registros_por_tabla"] == {"Cliente": 3, "Venta": 3}
    assert "INSERT INTO" in s["sql_script"].upper()


async def test_seeders_permisos_y_diagrama_vacio(cliente, equipo, db):
    otro = UsuarioRegistrado(nombre="Otro", email=f"otro_{equipo.pid}@test.local")
    db.add(otro)
    await db.commit()
    await _con_lienzo(equipo, db)
    assert (await cliente.como(otro).post("/api/ia/seeders/generar", json={"proyecto_id": equipo.pid})).status_code == 403
    r = await cliente.como(equipo.ana).post("/api/ia/seeders/generar", json={"diagram_json": {"nodes": []}})
    assert r.status_code == 400


# ─── Generar app móvil Flutter ──────────────────────────────────────────────

async def test_generar_preview_y_descargar_app_movil(cliente, equipo, db):
    await _con_lienzo(equipo, db)
    yo = cliente.como(equipo.lucia)

    r = await yo.post("/api/ia/app-movil/generar", json={"proyecto_id": equipo.pid})
    assert r.status_code == 200, r.text
    archivos = r.json()["archivos"]
    for esperado in ("lib/main.dart", "lib/models/cliente.dart", "lib/services/venta_service.dart",
                     "lib/views/venta/venta_form_view.dart"):
        assert esperado in archivos, esperado
    assert "class Cliente" in archivos["lib/models/cliente.dart"]

    assert (await yo.get(f"/api/ia/app-movil/preview/{equipo.pid}")).status_code == 200

    r = await yo.get(f"/api/ia/app-movil/descargar/{equipo.pid}")
    assert r.status_code == 200
    nombres = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
    assert any(n.endswith("lib/main.dart") for n in nombres) and any(n.endswith("pubspec.yaml") for n in nombres)


async def test_generar_app_movil_sin_clases_da_400(cliente, equipo, db):
    await _con_lienzo(equipo, db, {"nodes": [], "relations": []})
    r = await cliente.como(equipo.ana).post("/api/ia/app-movil/generar", json={"proyecto_id": equipo.pid})
    assert r.status_code == 400


async def test_refinar_vista_con_ia_simulada(cliente, equipo, db, monkeypatch):
    from backend.modules.gestion_asistencia_ia.generar_app_movil.controllers import app_movil_controller

    llamadas = []

    async def ia(vista_nombre, codigo_actual, instrucciones, api_endpoint=""):
        llamadas.append(instrucciones)
        return codigo_actual + "\n// boton agregado", "Se agregó un botón"

    monkeypatch.setattr(app_movil_controller, "refinar_codigo_con_ia", ia)
    cuerpo = {"proyecto_id": equipo.pid, "vista_nombre": "ClienteList", "codigo_actual": "class X {}",
              "instrucciones": "agrega un botón"}

    r = await cliente.como(equipo.beto).post("/api/ia/app-movil/refinar", json=cuerpo)
    assert r.status_code == 200, r.text
    assert r.json()["codigo_refinado"].endswith("// boton agregado")

    otro = UsuarioRegistrado(nombre="Otro", email=f"otro2_{equipo.pid}@test.local")
    db.add(otro)
    await db.commit()
    assert (await cliente.como(otro).post("/api/ia/app-movil/refinar", json=cuerpo)).status_code == 403, \
        "gasta tokens: solo miembros del proyecto"
    assert llamadas == ["agrega un botón"]
