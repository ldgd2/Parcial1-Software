"""Contexto que recibe la IA, parámetros por proveedor y manejo de respuestas (sin red: IA simulada)."""
import json
import types

import httpx
import pytest

from backend.modules.gestion_asistencia_ia.generar_diagrama_prompt.services import llm_client, prompt_service
from backend.modules.gestion_asistencia_ia.generar_diagrama_prompt.services.prompt_service import _pide_cambios


@pytest.fixture
def rescates(monkeypatch):
    """Registra si se llamó a los proveedores de rescate (Gemini/OpenRouter)."""
    llamadas = []

    async def gemini(prompt, context=None, api_key=None, **k):
        llamadas.append(("gemini", api_key))
        raise RuntimeError("sin red")

    async def openrouter(prompt, context=None, api_key=None, **k):
        llamadas.append(("openrouter", api_key))
        raise RuntimeError("sin red")

    monkeypatch.setattr(llm_client, "_consultar_gemini", gemini)
    monkeypatch.setattr(llm_client, "_consultar_openrouter", openrouter)
    return llamadas


# ─── Qué recibe la IA ───────────────────────────────────────────────────────

async def test_el_pedido_llega_sin_comprimir(cliente, equipo, ia):
    pedido = "Agrega la clase MétodoPago con fechaVencimiento y relaciónala hacia Venta"
    await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": pedido, "proyecto_id": equipo.pid})
    assert ia.prompts[-1]["prompt"] == pedido, "nombres con mayúsculas y acentos intactos"


async def test_el_diagrama_va_una_sola_vez_y_es_el_vivo(cliente, equipo, ia):
    # 1er pedido deja guardado un snapshot "viejo"
    await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "agrega Pago", "context": "Viejo(+id:int)", "proyecto_id": equipo.pid})
    # 2do pedido con el lienzo actual
    await cliente.post("/prompt/generar", json={"prompt": "agrega Envio", "context": "Venta(+id:int);Pago(+id:int)", "proyecto_id": equipo.pid})
    ctx = ia.prompts[-1]["context"]
    assert "[MEMORIA DEL PROYECTO" in ctx, "la memoria comprimida sigue llegando"
    assert "Diagrama actual (en vivo):\nVenta(+id:int);Pago(+id:int)" in ctx
    assert "Viejo(+id:int)" not in ctx, "no se mezcla el diagrama anterior con el actual"
    assert ctx.count("Venta(+id:int)") == 1


async def test_sin_lienzo_en_vivo_usa_el_ultimo_guardado(cliente, equipo, ia):
    await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "agrega Pago", "context": "Venta(+id:int)", "proyecto_id": equipo.pid})
    await cliente.post("/prompt/generar", json={"prompt": "agrega Envio", "proyecto_id": equipo.pid})
    assert "Último diagrama guardado: Venta(+id:int)" in ia.prompts[-1]["context"]


def test_mismo_mensaje_para_todos_los_proveedores():
    m = llm_client.armar_mensaje_usuario("agrega Pago", "Venta(+id:int)")
    assert m.startswith("Contexto del proyecto:\nVenta(+id:int)\n\nPedido del usuario:\nagrega Pago")
    assert "deletedRelations" in m
    sistema = llm_client.UNIVERSAL_SYSTEM_PROMPT
    for regla in ("MERGED BY CLASS NAME", "QUESTIONS", "rechazos/", "deletedRelations"):
        assert regla in sistema


def test_detecta_si_el_pedido_cambia_el_diagrama():
    assert _pide_cambios("agrega la clase Pago")
    assert _pide_cambios("elimina Envio")
    assert _pide_cambios("GENERAR DIAGRAMA DESDE REQUISITOS:\n...")
    assert _pide_cambios("diagrama de una biblioteca")
    assert not _pide_cambios("¿qué hace la clase Venta?"), "'hace' no es un pedido de cambio"
    assert not _pide_cambios("¿hacia dónde apunta la relación de Pago?")
    assert not _pide_cambios("¿qué clases tiene la unidad académica?"), "'unidad' no es 'unir'"
    assert _pide_cambios("¿puedes agregar la clase Pago?")
    assert _pide_cambios("relaciona Pago con Venta")
    assert not _pide_cambios("EXPLICACIÓN ARQUITECTÓNICA:\nExplica de manera didáctica la arquitectura")


# ─── Manejo de respuestas ───────────────────────────────────────────────────

async def test_una_pregunta_no_inventa_clases_ni_propuesta(cliente, equipo, ia, rescates):
    ia.respuesta = {"summary": "La clase Venta registra cada compra del Cliente con su Pago.", "nodes": [], "relations": []}
    r = await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "¿para qué sirve Venta?", "proyecto_id": equipo.pid})
    datos = r.json()
    assert datos["nodes"] == [], "no se extraen 'Cliente' ni 'Pago' de la explicación"
    assert "registra cada compra" in datos["summary"]
    assert rescates == [], "no se gasta en otros proveedores"
    if datos.get("version_id"):
        v = (await cliente.get(f"/api/ia/contexto/{equipo.pid}/versiones/{datos['version_id']}")).json()
        assert v["estado_propuesta"] is None, "una respuesta sin cambios no es propuesta"


async def test_solo_borrar_no_dispara_rescates(cliente, equipo, ia, rescates):
    ia.respuesta = {"summary": "Se eliminó Envio.", "nodes": [], "relations": [], "deletedNodes": ["Envio"],
                    "deletedRelations": [{"source": "Venta", "target": "Envio"}]}
    r = await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "elimina la clase Envio", "proyecto_id": equipo.pid})
    datos = r.json()
    assert rescates == []
    assert datos["deletedNodes"] == ["Envio"]
    assert datos["deletedRelations"] == [{"source": "Venta", "target": "Envio"}]
    v = (await cliente.get(f"/api/ia/contexto/{equipo.pid}/versiones/{datos['version_id']}")).json()
    assert v["estado_propuesta"] == "pendiente"


async def test_rescate_usa_la_llave_del_servidor_no_la_del_usuario(cliente, equipo, ia, rescates):
    ia.respuesta = {"summary": "No pude.", "nodes": []}
    await cliente.como(equipo.ana).post("/prompt/generar", json={
        "prompt": "agrega la clase Pago", "proyecto_id": equipo.pid, "provider": "kimi", "api_key": "sk-kimi-del-usuario"})
    assert rescates, "un pedido de cambio sin cambios sí intenta rescatar"
    assert all(llave is None for _, llave in rescates), rescates


async def test_respaldo_entre_proveedores_no_reenvia_la_llave(monkeypatch):
    usadas = []

    async def kimi_falla(*a, **k):
        raise RuntimeError("Kimi caído")

    async def gemini_ok(prompt, context=None, image_base64=None, image_mime_type="image/png", api_key=None):
        usadas.append(api_key)
        return json.dumps({"summary": "ok", "nodes": [{"name": "Pago"}]})

    monkeypatch.setattr(llm_client, "_consultar_kimi", kimi_falla)
    monkeypatch.setattr(llm_client, "_consultar_gemini", gemini_ok)
    monkeypatch.setattr(llm_client.settings, "GEMINI_API", "llave-del-servidor")
    monkeypatch.setattr(llm_client.settings, "OPENROUTE_API", "")
    _, proveedor = await llm_client.consultar_llm("agrega Pago", provider="kimi", api_key="sk-kimi-del-usuario")
    assert proveedor == "gemini (fallback)"
    assert usadas == [None], "la llave de Kimi del usuario no se manda a Google"


# ─── Parámetros por proveedor (HTTP simulado) ───────────────────────────────

def _cliente_simulado(monkeypatch, responder):
    pedidos = []
    original = httpx.AsyncClient

    def manejar(request: httpx.Request):
        pedidos.append(request)
        return responder(request)

    # Solo dentro de llm_client (no el módulo httpx global: lo usa también el cliente de los tests)
    falso = types.SimpleNamespace(
        AsyncClient=lambda *a, **k: original(transport=httpx.MockTransport(manejar), timeout=k.get("timeout")),
        RequestError=httpx.RequestError,
    )
    monkeypatch.setattr(llm_client, "httpx", falso)
    return pedidos


async def test_kimi_usa_el_modelo_configurado_y_corta_con_llave_invalida(monkeypatch):
    monkeypatch.setattr(llm_client.settings, "KIMI_MODEL", "kimi-k3.1-pro")
    pedidos = _cliente_simulado(monkeypatch, lambda r: httpx.Response(401, json={"error": "invalid key"}))
    with pytest.raises(Exception):
        await llm_client._consultar_kimi("agrega Pago", api_key="mala")
    modelos = [json.loads(p.content)["model"] for p in pedidos]
    assert modelos[0] == "kimi-k3.1-pro", "primero el modelo configurado"
    assert len(pedidos) == 2, f"con 401 no sigue probando modelos (fueron {len(pedidos)})"


async def test_kimi_devuelve_el_json(monkeypatch):
    cuerpo = {"choices": [{"message": {"content": '{"summary":"ok","nodes":[{"name":"Pago"}]}'}}]}
    pedidos = _cliente_simulado(monkeypatch, lambda r: httpx.Response(200, json=cuerpo))
    texto = await llm_client._consultar_kimi("agrega Pago", context="Venta(+id:int)", api_key="k")
    assert json.loads(texto)["nodes"][0]["name"] == "Pago"
    payload = json.loads(pedidos[0].content)
    assert payload["max_tokens"] == llm_client.MAX_TOKENS_SALIDA
    assert payload["messages"][0]["content"] == llm_client.UNIVERSAL_SYSTEM_PROMPT
    assert "Pedido del usuario:\nagrega Pago" in payload["messages"][1]["content"]


async def test_openrouter_no_corta_diagramas_medianos(monkeypatch):
    cuerpo = {"choices": [{"message": {"content": '{"summary":"ok","nodes":[{"name":"Pago"}]}'}}]}
    pedidos = _cliente_simulado(monkeypatch, lambda r: httpx.Response(200, json=cuerpo))
    await llm_client._consultar_openrouter("agrega Pago", api_key="k")
    payload = json.loads(pedidos[0].content)
    assert payload["max_tokens"] == 8192, "antes era 2000 y el JSON llegaba cortado"
    assert payload["temperature"] == 0.2 and payload["response_format"] == {"type": "json_object"}


# ─── Equilibrio de tokens: medición real y tope de llamadas por pedido ──────

def _respuesta_por_proveedor(contenido_kimi: str, contenido_otros: str):
    def responder(request: httpx.Request):
        url = str(request.url)
        if "moonshot" in url:
            return httpx.Response(200, json={"choices": [{"message": {"content": contenido_kimi}}],
                                             "usage": {"prompt_tokens": 1500, "completion_tokens": 300}})
        if "generativelanguage" in url:
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": contenido_otros}]}}],
                                             "usageMetadata": {"promptTokenCount": 1400, "candidatesTokenCount": 200, "thoughtsTokenCount": 50}})
        return httpx.Response(200, json={"choices": [{"message": {"content": contenido_otros}}],
                                         "usage": {"prompt_tokens": 1450, "completion_tokens": 250}})
    return responder


@pytest.fixture
def llaves(monkeypatch):
    for nombre, valor in (("KIMI_API", "k"), ("GEMINI_API", "g"), ("OPENROUTE_API", "o"), ("KIMI_MODEL", "kimi-k3.1-pro")):
        monkeypatch.setattr(llm_client.settings, nombre, valor)


async def test_un_pedido_normal_es_una_sola_llamada_y_se_mide(cliente, equipo, monkeypatch, llaves):
    ok = '{"summary":"Se agregó Pago.","nodes":[{"name":"Pago","attributes":["+id:int"]}],"relations":[]}'
    pedidos = _cliente_simulado(monkeypatch, _respuesta_por_proveedor(ok, ok))
    r = await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "agrega Pago", "proyecto_id": equipo.pid, "provider": "kimi"})
    uso = r.json()["uso_tokens"]
    assert len(pedidos) == 1
    assert uso["llamadas"] == 1 and uso["entrada"] == 1500 and uso["salida"] == 300
    assert uso["proveedores"] == ["kimi:kimi-k3.1-pro"] and uso["estimado"] is False


async def test_un_pedido_que_falla_no_pasa_de_3_llamadas(cliente, equipo, monkeypatch, llaves):
    # Todas las IA responden algo sin clases: antes eran ~6 llamadas cobradas (Kimi ×4, Gemini, OpenRouter, rescates)
    vacio = '{"summary":"No entendí bien el pedido, ¿puedes dar más detalle?","nodes":[]}'
    pedidos = _cliente_simulado(monkeypatch, _respuesta_por_proveedor(vacio, vacio))
    r = await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "agrega la clase Pago", "proyecto_id": equipo.pid, "provider": "kimi"})
    assert r.status_code == 200, r.text
    uso = r.json()["uso_tokens"]
    assert uso["llamadas"] <= llm_client.MAX_LLAMADAS_POR_PEDIDO
    cobradas = [p for p in pedidos]   # todas responden 200 = todas se cobran
    assert len(cobradas) <= llm_client.MAX_LLAMADAS_POR_PEDIDO, [str(p.url).split("?")[0] for p in cobradas]


async def test_respaldo_a_gemini_no_se_repite_en_el_rescate(cliente, equipo, monkeypatch, llaves):
    ok = '{"summary":"ok","nodes":[{"name":"Pago"}]}'

    def responder(request):
        if "moonshot" in str(request.url):
            return httpx.Response(500, json={"error": "caído"})
        return _respuesta_por_proveedor(ok, '{"summary":"sin clases","nodes":[]}')(request)

    pedidos = _cliente_simulado(monkeypatch, responder)
    await cliente.como(equipo.ana).post("/prompt/generar", json={"prompt": "agrega la clase Pago", "proyecto_id": equipo.pid, "provider": "kimi"})
    a_gemini = [p for p in pedidos if "generativelanguage" in str(p.url)]
    assert len(a_gemini) == 1, "Gemini ya respondió como respaldo: el rescate no debe volver a llamarlo"
