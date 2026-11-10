"""
Interfaz de la app Flutter generada: una APP (inicio con resumen, módulos, ajustes, detalle,
formularios con los controles adecuados, acciones de negocio y animaciones), no un
administrador de tablas.

Las pantallas fijas viven en templates/flutter_ui (Dart real, fácil de mantener); lo que depende
del diagrama (por entidad) se arma aquí a partir de templates/flutter_ui_entidad.
"""
import os
import re
from typing import Dict, List, Optional

_TPL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
_TPL_APP = os.path.join(_TPL, "flutter_ui")
_TPL_ENTIDAD = os.path.join(_TPL, "flutter_ui_entidad")

_DINERO = re.compile(r"(precio|monto|total|costo|coste|importe|salario|sueldo|pago|saldo|tarifa|price|amount|cost)", re.I)
_EMAIL = re.compile(r"(email|correo|mail)", re.I)
_TELEFONO = re.compile(r"(telefono|celular|movil|phone|whatsapp)", re.I)
_LARGO = re.compile(r"(descripcion|detalle|observacion|nota|comentario|direccion|resumen|contenido)", re.I)
_ESTADO = re.compile(r"(estado|status|tipo|categoria|prioridad|nivel|rol)", re.I)
_TITULOS = ["nombre", "nombrecompleto", "name", "titulo", "title", "razonsocial", "descripcion", "codigo", "email", "correo"]
_SUBTITULOS = ["email", "correo", "descripcion", "telefono", "celular", "direccion", "categoria", "tipo", "estado"]


# ── utilidades ────────────────────────────────────────────────────────────────

def dart_str(texto: str) -> str:
    """Contenido seguro para un literal Dart entre comillas simples."""
    return str(texto).replace("\\", "\\\\").replace("'", "\\'").replace("$", "\\$").replace("\n", " ")


def etiqueta(identificador: str) -> str:
    """camelCase / snake_case → "Fecha ingreso"."""
    palabras = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(identificador)).replace("_", " ").split()
    if not palabras:
        return str(identificador)
    texto = " ".join(p.lower() for p in palabras)
    return texto[0].upper() + texto[1:]


def plural(nombre: str) -> str:
    """Plural en español de la primera palabra ("Detalle pedido" → "Detalles pedido")."""
    partes = nombre.split(" ", 1)
    p = partes[0]
    if re.search(r"[aeiouáéó]$", p, re.I):
        p += "s"
    elif p.lower().endswith("z"):
        p = p[:-1] + "ces"
    elif not p.lower().endswith("s"):
        p += "es"
    return " ".join([p] + partes[1:])


def _tipo_campo(attr: dict) -> str:
    base = attr["base_tipo"]
    if base == "int":
        return "entero"
    if base == "double":
        return "dinero" if _DINERO.search(attr["nombre"]) else "decimal"
    if base == "bool":
        return "booleano"
    if base == "DateTime":
        return "fecha"
    return "texto"


def _icono_campo(attr: dict) -> str:
    n, k = attr["nombre"], attr["kind"]
    if k == "dinero":
        return "Icons.payments_outlined"
    if k == "fecha":
        return "Icons.event_outlined"
    if k == "booleano":
        return "Icons.toggle_on_outlined"
    if k in ("entero", "decimal"):
        return "Icons.numbers_rounded"
    if _EMAIL.search(n):
        return "Icons.alternate_email_rounded"
    if _TELEFONO.search(n):
        return "Icons.phone_outlined"
    if re.search(r"direccion|ubicacion|ciudad", n, re.I):
        return "Icons.place_outlined"
    if _ESTADO.search(n):
        return "Icons.flag_outlined"
    if re.search(r"nombre|name|titulo", n, re.I):
        return "Icons.badge_outlined"
    return "Icons.notes_rounded"


def _valor(attr: dict, var: str = "e") -> str:
    """Expresión Dart que muestra el valor ya formateado."""
    campo = f"{var}.{attr['nombre']}"
    return {
        "texto": f"Fmt.texto({campo})",
        "entero": f"Fmt.numero({campo})",
        "decimal": f"Fmt.numero({campo})",
        "dinero": f"Fmt.dinero({campo})",
        "booleano": f"Fmt.si({campo})",
        "fecha": f"Fmt.fecha({campo})",
    }[attr["kind"]]


def _con_etiqueta(attr: dict) -> str:
    return f"'{dart_str(attr['etiqueta'])}: ${{{_valor(attr)}}}'"


def _tipo_param(java: str) -> str:
    return {
        "Integer": "entero", "Long": "entero", "Short": "entero",
        "Double": "decimal", "java.math.BigDecimal": "decimal",
        "Boolean": "booleano",
        "java.time.LocalDate": "fecha", "java.time.LocalDateTime": "fechahora",
    }.get(java, "texto")


def _sin_import_si_no_se_usa(codigo: str, linea_import: str, simbolo: str) -> str:
    cuerpo = codigo.replace(linea_import, "")
    return codigo if simbolo in cuerpo else cuerpo


def _llenar(plantilla: str, valores: Dict[str, str]) -> str:
    # Primero las claves largas: __PASCAL__ no debe pisar __PASCAL__Ui, etc. (todas cerradas con __)
    for clave in sorted(valores, key=len, reverse=True):
        plantilla = plantilla.replace(f"__{clave}__", valores[clave])
    return plantilla


# ── análisis de cada entidad ──────────────────────────────────────────────────

def preparar_entidad(clase: dict, meta: dict) -> dict:
    """Agrega a la clase (de _extraer_clases_diagrama) lo necesario para la interfaz."""
    campos = []
    for a in clase["atributos"]:
        if a.get("es_pk"):
            continue
        c = dict(a)
        c["kind"] = _tipo_campo(a)
        c["etiqueta"] = etiqueta(a.get("nombre_visible") or a["nombre"])
        c["icono"] = _icono_campo(c)
        campos.append(c)

    textos = [c for c in campos if c["kind"] == "texto"]

    def elegir(preferidos, candidatos, excluir=()):
        disponibles = [c for c in candidatos if c["nombre"] not in excluir]
        for p in preferidos:
            for c in disponibles:
                if c["nombre"].lower() == p:
                    return c
        return disponibles[0] if disponibles else None

    titulo = elegir(_TITULOS, textos)
    excluir = {titulo["nombre"]} if titulo else set()
    subtitulo = elegir(_SUBTITULOS, textos, excluir)
    if subtitulo:
        excluir.add(subtitulo["nombre"])

    orden = {"dinero": 0, "texto": 1, "booleano": 2, "fecha": 3, "entero": 4, "decimal": 5}
    destacables = [c for c in campos if c["nombre"] not in excluir
                   and (c["kind"] != "texto" or _ESTADO.search(c["nombre"]))]
    destacados = sorted(destacables, key=lambda c: orden[c["kind"]])[:3]

    nombre_visible = etiqueta(clase["nombre_pascal"])
    return {
        **clase,
        "campos": campos,
        "titulo": titulo,
        "subtitulo": subtitulo,
        "destacados": destacados,
        "nombre_visible": nombre_visible,
        "plural_visible": plural(nombre_visible),
        "icono": meta["icon"],
        "color": meta["color"],
        "descripcion": meta["desc"],
    }


# ── archivos por entidad ──────────────────────────────────────────────────────

def _ui_dart(e: dict) -> str:
    P, S = e["nombre_pascal"], e["nombre_snake"]

    if e["titulo"] is None:
        titulo = f"'{dart_str(e['nombre_visible'])} ${{e.id.length > 6 ? e.id.substring(0, 6) : e.id}}'"
    elif e["titulo"]["kind"] == "texto":
        n = e["titulo"]["nombre"]
        titulo = f"e.{n}.trim().isEmpty ? 'Sin nombre' : e.{n}.trim()"
    else:
        titulo = _valor(e["titulo"])

    s = e["subtitulo"]
    if s is None:
        subtitulo = "''"
    elif s["kind"] == "texto":
        subtitulo = f"e.{s['nombre']}.trim()"
    else:
        subtitulo = _con_etiqueta(s)

    def chip(c):
        if c["kind"] in ("booleano", "entero", "decimal"):
            texto = _con_etiqueta(c)
        else:
            texto = _valor(c)
        return f"CampoVista('{dart_str(c['etiqueta'])}', {texto}, {c['icono']})"

    destacados = ",\n        ".join(chip(c) for c in e["destacados"])
    campos = ",\n        ".join(
        f"CampoVista('{dart_str(c['etiqueta'])}', {_valor(c)}, {c['icono']})" for c in e["campos"])
    busqueda = " ".join(f"${{{_valor(c)}}}" for c in e["campos"]) or "${e.id}"

    acciones = []
    for m in e.get("metodos", []):
        params = ", ".join(
            f"ParamInfo('{p['nombre']}', '{dart_str(etiqueta(p.get('nombre_visible') or p['nombre']))}', '{_tipo_param(p['tipo'])}')"
            for p in m["parametros"])
        acciones.append(
            "AccionInfo(\n"
            f"          nombre: '{m['nombre']}',\n"
            f"          etiqueta: '{dart_str(etiqueta(m.get('nombre_visible') or m['nombre']))}',\n"
            f"          retorno: '{dart_str(m['retorno'])}',\n"
            f"          parametros: const [{params}],\n"
            f"          ejecutar: (p) => s.accion('{m['nombre']}', p),\n"
            "        )")
    acciones_dart = ("[\n        " + ",\n        ".join(acciones) + ",\n      ]") if acciones else "const []"

    codigo = f"""import 'package:flutter/material.dart';

import '../../app/modulo.dart';
import '../../core/utils/fmt.dart';
import '../../models/{S}.dart';
import '../../services/{S}_service.dart';

/// Cómo se muestra {dart_str(e['nombre_visible'])} en la app: título, datos destacados y acciones.
class {P}Ui {{
  static const String nombre = '{dart_str(e['nombre_visible'])}';
  static const String plural = '{dart_str(e['plural_visible'])}';
  static const IconData icono = {e['icono']};
  static const Color color = Color({e['color']});

  static String titulo({P} e) => {titulo};

  static String subtitulo({P} e) => {subtitulo};

  static List<CampoVista> destacados({P} e) => [
        {destacados}
      ];

  static List<CampoVista> campos({P} e) => [
        {campos}
      ];

  static bool coincide({P} e, String q) => '{busqueda}'.toLowerCase().contains(q);

  /// Métodos del diagrama: el backend los expone como POST /api/.../<método>
  static List<AccionInfo> acciones({P}Service s) => {acciones_dart};
}}
"""
    return _sin_import_si_no_se_usa(codigo, "import '../../core/utils/fmt.dart';\n", "Fmt.")


def _form_partes(e: dict) -> Dict[str, str]:
    decl, ini, disp, campos, payload = [], [], [], [], []
    hay_fecha = False
    for i, c in enumerate(e["campos"], start=1):
        n, k = c["nombre"], c["kind"]
        var = n[0].upper() + n[1:]
        lbl = dart_str(c["etiqueta"])
        obligatorio = e["titulo"] is not None and n == e["titulo"]["nombre"]
        if k in ("texto", "entero", "decimal", "dinero"):
            ctl = f"_c{var}"
            decl.append(f"  final {ctl} = TextEditingController();")
            ini.append(f"      {ctl}.text = item.{n}.toString();" if k != "texto" else f"      {ctl}.text = item.{n};")
            disp.append(f"    {ctl}.dispose();")
            validaciones = []
            if obligatorio:
                validaciones.append(f"if (t.isEmpty) return 'Completa {lbl.lower()}';")
            if k == "texto" and _EMAIL.search(n):
                validaciones.append("if (t.isNotEmpty && !t.contains('@')) return 'Correo no válido';")
                teclado = "TextInputType.emailAddress"
            elif k == "texto" and _TELEFONO.search(n):
                teclado = "TextInputType.phone"
            elif k == "entero":
                validaciones.append("if (t.isNotEmpty && int.tryParse(t) == null) return 'Debe ser un número entero';")
                teclado = "TextInputType.number"
            elif k in ("decimal", "dinero"):
                validaciones.append("if (t.isNotEmpty && double.tryParse(t.replaceAll(',', '.')) == null) return 'Debe ser un número';")
                teclado = "const TextInputType.numberWithOptions(decimal: true)"
            else:
                teclado = "TextInputType.multiline" if _LARGO.search(n) else "TextInputType.text"
            formateadores = ""
            if k == "entero":
                formateadores = "\n                inputFormatters: [FilteringTextInputFormatter.digitsOnly],"
            elif k in ("decimal", "dinero"):
                formateadores = "\n                inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.,]'))],"
            validador = ""
            if validaciones:
                validador = ("\n                validator: (v) {\n                  final t = (v ?? '').trim();\n                  "
                             + "\n                  ".join(validaciones) + "\n                  return null;\n                },")
            if k == "dinero":
                deco = f"InputDecoration(labelText: '{lbl}', prefixIcon: const Icon({c['icono']}), prefixText: '${{Fmt.moneda}} ')"
            else:
                deco = f"const InputDecoration(labelText: '{lbl}{' *' if obligatorio else ''}', prefixIcon: Icon({c['icono']}))"
            lineas = "3" if (k == "texto" and _LARGO.search(n)) else "1"
            widget = (f"TextFormField(\n                controller: {ctl},\n                decoration: {deco},\n"
                      f"                keyboardType: {teclado},\n                maxLines: {lineas},\n"
                      f"                textCapitalization: {'TextCapitalization.sentences' if k == 'texto' and not _EMAIL.search(n) else 'TextCapitalization.none'},"
                      f"{formateadores}{validador}\n              )")
            if k == "texto":
                payload.append(f"      '{n}': {ctl}.text.trim(),")
            elif k == "entero":
                payload.append(f"      '{n}': int.tryParse({ctl}.text.trim()),")
            else:
                payload.append(f"      '{n}': double.tryParse({ctl}.text.trim().replaceAll(',', '.')),")
        elif k == "booleano":
            var_b = f"_b{var}"
            decl.append(f"  bool {var_b} = false;")
            ini.append(f"      {var_b} = item.{n};")
            widget = (f"Container(\n                decoration: BoxDecoration(\n"
                      f"                  color: Theme.of(context).inputDecorationTheme.fillColor,\n"
                      f"                  borderRadius: BorderRadius.circular(16),\n                ),\n"
                      f"                child: SwitchListTile(\n                  secondary: const Icon({c['icono']}),\n"
                      f"                  title: const Text('{lbl}'),\n                  value: {var_b},\n"
                      f"                  onChanged: (v) => setState(() => {var_b} = v),\n                ),\n              )")
            payload.append(f"      '{n}': {var_b},")
        else:  # fecha
            hay_fecha = True
            var_f = f"_f{var}"
            decl.append(f"  DateTime? {var_f};")
            ini.append(f"      {var_f} = item.{n};")
            widget = (f"InkWell(\n                borderRadius: BorderRadius.circular(16),\n"
                      f"                onTap: () => _elegirFecha({var_f}, (d) => {var_f} = d),\n"
                      f"                child: InputDecorator(\n"
                      f"                  decoration: const InputDecoration(labelText: '{lbl}', prefixIcon: Icon({c['icono']}), suffixIcon: Icon(Icons.expand_more_rounded)),\n"
                      f"                  child: Text(Fmt.fecha({var_f})),\n                ),\n              )")
            largo = 10 if c.get("java_tipo") == "java.time.LocalDate" else 19
            payload.append(f"      '{n}': {var_f}?.toIso8601String().substring(0, {largo}),")
        campos.append(f"            FadeSlideIn(\n              index: {i},\n              child: Padding(\n"
                      f"                padding: const EdgeInsets.only(bottom: 14),\n              child: {widget},\n              ),\n            ),")
    return {
        "DECLARACIONES": "\n".join(decl),
        "INICIALES": "\n".join(ini),
        "DISPOSE": "\n".join(disp),
        "CAMPOS": "\n".join(campos),
        "PAYLOAD": "\n".join(payload),
        "_hay_fecha": "1" if hay_fecha else "",
    }


def _leer(ruta: str) -> str:
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def archivos_entidad(e: dict) -> Dict[str, str]:
    base = {
        "PASCAL": e["nombre_pascal"],
        "SNAKE": e["nombre_snake"],
        "NOMBRE": dart_str(e["nombre_visible"]),
        "NOMBRE_MIN": dart_str(e["nombre_visible"].lower()),
    }
    S = e["nombre_snake"]
    lista = _llenar(_leer(os.path.join(_TPL_ENTIDAD, "list_view.dart.tpl")), base)
    detalle = _llenar(_leer(os.path.join(_TPL_ENTIDAD, "detail_view.dart.tpl")), base)

    partes = _form_partes(e)
    hay_fecha = partes.pop("_hay_fecha")
    form = _llenar(_leer(os.path.join(_TPL_ENTIDAD, "form_view.dart.tpl")), {**base, **partes})
    if not hay_fecha:
        form = re.sub(r"  Future<void> _elegirFecha\(.*?\n  }\n\n", "", form, flags=re.S)
    if not e["campos"]:
        form = form.replace("    final item = widget.item;\n    if (item != null) {\n\n    }\n", "")
    form = _sin_import_si_no_se_usa(form, "import '../../core/utils/fmt.dart';\n", "Fmt.")
    form = _sin_import_si_no_se_usa(form, "import '../../models/" + S + ".dart';\n", e["nombre_pascal"] + "?")

    return {
        f"lib/views/{S}/{S}_ui.dart": _ui_dart(e),
        f"lib/views/{S}/{S}_list_view.dart": lista,
        f"lib/views/{S}/{S}_detail_view.dart": detalle,
        f"lib/views/{S}/{S}_form_view.dart": form,
    }


def _registro_modulos(entidades: List[dict]) -> str:
    imports, items = [], []
    for e in entidades:
        P, S = e["nombre_pascal"], e["nombre_snake"]
        imports += [
            f"import '../services/{S}_service.dart';",
            f"import '../views/{S}/{S}_form_view.dart';",
            f"import '../views/{S}/{S}_list_view.dart';",
            f"import '../views/{S}/{S}_ui.dart';",
        ]
        items.append(f"""  ModuloInfo(
    nombre: {P}Ui.nombre,
    plural: {P}Ui.plural,
    descripcion: '{dart_str(e['descripcion'])}',
    icono: {P}Ui.icono,
    color: {P}Ui.color,
    contar: () async => (await {P}Service().getAll()).length,
    recientes: () async =>
        (await {P}Service().getAll()).take(5).map((e) => ResumenItem({P}Ui.titulo(e), {P}Ui.subtitulo(e))).toList(),
    lista: () => const {P}ListView(),
    nuevo: () => const {P}FormView(),
    acciones: {P}Ui.acciones({P}Service()),
  ),""")
    return ("import 'modulo.dart';\n" + "\n".join(imports) +
            "\n\n/// Módulos de la app: uno por cada clase del diagrama.\nfinal List<ModuloInfo> modulos = [\n"
            + "\n".join(items) + "\n];\n")


# ── punto de entrada ──────────────────────────────────────────────────────────

def archivos_interfaz(entidades: List[dict], titulo_app: str, subtitulo_app: str, icono_hero: str,
                      color_marca: Optional[str] = None) -> Dict[str, str]:
    """Todos los archivos de interfaz (lib/...) listos para escribir."""
    valores = {
        "APP_TITLE": dart_str(titulo_app),
        "APP_SUBTITLE": dart_str(subtitulo_app),
        "HERO_ICON": icono_hero,
        "SEED": color_marca or (entidades[0]["color"] if entidades else "0xFF6366F1"),
    }
    archivos: Dict[str, str] = {}
    for raiz, _, nombres in os.walk(_TPL_APP):
        for nombre in nombres:
            ruta = os.path.join(raiz, nombre)
            relativa = os.path.relpath(ruta, _TPL_APP).replace("\\", "/")
            archivos[relativa] = _llenar(_leer(ruta), valores)
    for e in entidades:
        archivos.update(archivos_entidad(e))
    archivos["lib/app/modulos.dart"] = _registro_modulos(entidades)
    return archivos
