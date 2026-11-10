"""Tareas propuestas por la IA (simulada), estimación de esfuerzo y lectura de PDF de requisitos."""
import base64

from sqlalchemy import text

from backend.modules.gestion_usuarios.models import estimar_tarea


def test_estimacion_de_esfuerzo():
    assert estimar_tarea("diagrama", "Modelar Pago") == (2, "baja") or estimar_tarea("diagrama", "Modelar Pago")[1] != "alta"
    assert estimar_tarea("desarrollo", "Integrar pasarela de pagos")[1] == "alta"
    assert estimar_tarea("desarrollo", "x", horas_ia=12, complejidad_ia="media") == (12, "media")
    horas, complejidad = estimar_tarea("desarrollo", "x", horas_ia=999)
    assert 1 <= horas <= 40 and complejidad in ("baja", "media", "alta")


async def _repartir(cliente, equipo, monkeypatch, persistir):
    from backend.modules.gestion_proyectos_asistida.repartir_tareas.services import tareas_service

    async def ia_tareas(prompt, provider=None, api_key=None):
        assert "Ana Test" in prompt and "Beto Test" in prompt, "la IA recibe al equipo"
        return {"tareas": [
            {"usuario_id": equipo.ana.id, "tipo": "diagrama", "area": "modelado", "titulo": "Modelar Venta", "orden": 1},
            {"usuario_id": equipo.beto.id, "tipo": "desarrollo", "area": "backend", "titulo": "API de pagos",
             "estimacion_horas": 6, "complejidad": "media", "orden": 2},
        ]}

    monkeypatch.setattr(tareas_service, "_llamar_ia_tareas", ia_tareas)
    r = await cliente.como(equipo.ana).post("/api/ia/tareas/repartir", json={"proyecto_id": equipo.pid, "persistir": persistir})
    assert r.status_code == 200, r.text
    return r.json()


async def test_tareas_propuestas_no_se_crean_hasta_aprobar(cliente, equipo, monkeypatch, db, eventos_notif):
    datos = await _repartir(cliente, equipo, monkeypatch, persistir=False)
    assert {t["titulo"] for t in datos["tareas"]} == {"Modelar Venta", "API de pagos"}
    n = (await db.execute(text("SELECT count(*) FROM tareas_ia WHERE proyecto_id = :p"), {"p": equipo.pid})).scalar()
    assert n == 0, "con persistir=False la IA solo propone"
    assert eventos_notif == []


async def test_tareas_aprobadas_se_crean_con_estimacion(cliente, equipo, monkeypatch, db, eventos_notif):
    await _repartir(cliente, equipo, monkeypatch, persistir=True)
    filas = (await db.execute(text(
        "SELECT titulo, usuario_id, estimacion_horas, complejidad FROM tareas_ia WHERE proyecto_id = :p ORDER BY orden"
    ), {"p": equipo.pid})).all()
    assert [(f[0], f[1]) for f in filas] == [("Modelar Venta", equipo.ana.id), ("API de pagos", equipo.beto.id)]
    assert filas[1][2:] == (6, "media"), "respeta la estimación de la IA"
    assert filas[0][2] and filas[0][3], "si la IA no estima, se calcula"
    assert sorted(e["usuario_id"] for e in eventos_notif) == sorted([equipo.ana.id, equipo.beto.id])


def _pdf_con_texto(linea: str) -> bytes:
    """PDF mínimo válido de una página con una línea de texto."""
    contenido = f"BT /F1 12 Tf 72 720 Td ({linea}) Tj ET".encode()
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(contenido)).encode() + b" >>\nstream\n" + contenido + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    salida = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objetos, 1):
        offsets.append(len(salida))
        salida += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        salida += f"{off:010d} 00000 n \n".encode()
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return bytes(salida)


async def test_extraer_texto_de_pdf(cliente, equipo):
    cliente.como(equipo.ana)   # sesión obligatoria: la ruta usa recursos del servidor
    pdf = base64.b64encode(_pdf_con_texto("El sistema registra ventas y clientes")).decode()
    r = await cliente.post("/prompt/extraer-texto-pdf", json={"pdf_base64": f"data:application/pdf;base64,{pdf}"})
    assert r.status_code == 200, r.text
    assert "registra ventas y clientes" in r.json()["texto"]

    malo = await cliente.post("/prompt/extraer-texto-pdf", json={"pdf_base64": base64.b64encode(b"no soy un pdf").decode()})
    assert malo.status_code == 400
