import io
import os
import re
import shutil
import zipfile
from typing import Dict, List, Any, Tuple

from backend.modules.gestion_asistencia_ia.generar_app_movil.services.flutter_skeleton_service import (
    construir_archivos_esqueleto,
)
from backend.modules.gestion_asistencia_ia.exportar_github.services.parser_service import (
    RESERVED_CRUD_METHODS,
    map_java_type,
    parse_java_parameters,
    sanitize_identifier,
)
from backend.modules.gestion_asistencia_ia.generar_app_movil.services.flutter_ui_service import (
    archivos_interfaz,
    preparar_entidad,
)


def _to_snake_case(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]", " ", str(name)).strip()
    words = cleaned.split()
    if not words:
        return "entidad"
    s = words[0].lower() + "".join(w.capitalize() for w in words[1:])
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


def _to_pascal_case(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]", " ", str(name)).strip()
    words = cleaned.split()
    if not words:
        return "Entidad"
    return "".join(w.capitalize() for w in words)


def _to_camel_case(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]", " ", str(name)).strip()
    words = cleaned.split()
    if not words:
        return "attr"
    first = words[0]
    res = (first[0].lower() + first[1:]) + "".join(w.capitalize() for w in words[1:])
    if res[0].isdigit():
        res = f"field_{res}"
    return res


_CAMPOS_DE_AUDITORIA = {"id", "createdat", "updatedat", "isactive"}

# Tipo Java del backend generado -> (tipo Dart declarado, tipo base)
_JAVA_A_DART = {
    "Integer": ("int", "int"), "Long": ("int", "int"), "Short": ("int", "int"),
    "Double": ("double", "double"), "java.math.BigDecimal": ("double", "double"),
    "Boolean": ("bool", "bool"),
    "java.time.LocalDate": ("DateTime?", "DateTime"),
    "java.time.LocalDateTime": ("DateTime?", "DateTime"),
}


def _map_to_dart_type(tipo_uml: str) -> Tuple[str, str]:
    """Mismo criterio que el backend Spring (parser_service.map_java_type): así el JSON encaja."""
    return _JAVA_A_DART.get(map_java_type(tipo_uml or ""), ("String", "String"))


def _extraer_clases_diagrama(diagram_json: dict) -> List[dict]:
    """Clases del diagrama con los MISMOS nombres que usa el backend generado:
    - endpoint  = /api/<NombreClaseSinSimbolos en minúsculas>s  (Controller.java.jinja)
    - campos    = sanitize_identifier(nombre) (claves del JSON de Jackson)
    - id        = siempre `id` (UUID en el backend, String aquí); createdAt/updatedAt/isActive
                  y los atributos marcados PK los gestiona el backend, no el formulario.
    """
    nodos = diagram_json.get("nodes", []) if isinstance(diagram_json, dict) else []
    clases = []

    for nodo in nodos:
        tipo_nodo = str(nodo.get("type", "")).lower()
        if tipo_nodo in ["class", "interface", "clase"]:
            raw_nombre = str(nodo.get("nombre") or nodo.get("name") or "Entidad").strip()
            pascal = _to_pascal_case(raw_nombre)
            snake = _to_snake_case(raw_nombre)
            nombre_backend = re.sub(r"[^a-zA-Z0-9]", "", raw_nombre).capitalize() or "Entidad"

            atributos = [{"nombre": "id", "tipo": "String", "base_tipo": "String",
                          "java_tipo": "UUID", "es_pk": True}]
            vistos = {"id"}
            for a in nodo.get("atributos", []):
                nombre_raw = a.get("nombre") or a.get("name") or ""
                attr_name = sanitize_identifier(nombre_raw)
                if attr_name.lower() in _CAMPOS_DE_AUDITORIA or attr_name in vistos:
                    continue
                if a.get("visibilidad") == "PK":
                    continue  # en el backend es un UUID interno, no un dato que el usuario escriba
                tipo_raw = a.get("tipo") or a.get("type") or "String"
                dart_type, base_type = _map_to_dart_type(tipo_raw)
                atributos.append({
                    "nombre": attr_name,
                    "nombre_visible": _nombre_visible(nombre_raw),
                    "tipo": dart_type,
                    "base_tipo": base_type,
                    "java_tipo": map_java_type(tipo_raw),
                    "es_pk": False,
                })
                vistos.add(attr_name)

            clases.append({
                "id": nodo.get("id"),
                "nombre_pascal": pascal,
                "nombre_snake": snake,
                "endpoint": f"/api/{nombre_backend.lower()}s",
                "atributos": atributos,
                "metodos": _extraer_metodos(nodo),
            })

    return clases


def _nombre_visible(raw: str) -> str:
    """Nombre tal como se escribió en el diagrama (sanitize_identifier lo deja en minúsculas:
    fechaIngreso -> fechaingreso), solo para mostrarlo en pantalla."""
    texto = re.sub(r"^[\-\+#~\s]+", "", str(raw or "")).split(":")[0].strip()
    texto = re.sub(r"[^a-zA-Z0-9_ ]", " ", texto).strip()
    return texto or str(raw or "")


def _extraer_metodos(nodo: dict) -> List[dict]:
    """Métodos de negocio tal como los expone el backend: POST /api/<entidad>/<método>?param=valor."""
    metodos, vistos = [], set()
    for m in nodo.get("metodos", []) or []:
        nombre_raw = m.get("nombre") or m.get("name") or ""
        nombre = sanitize_identifier(nombre_raw)
        if not nombre or nombre == "unnamed" or nombre.lower() in RESERVED_CRUD_METHODS or nombre in vistos:
            continue
        vistos.add(nombre)
        retorno = str(m.get("retorno") or m.get("tipoRetorno") or "void").strip()
        retorno = "void" if retorno.lower() == "void" else map_java_type(retorno)
        params_raw = str(m.get("parametros", "") or "")
        java_decl = parse_java_parameters(params_raw, nombre)[0]
        partes_raw = [p.strip() for p in params_raw.split(",") if p.strip()]
        parametros = []
        for i, decl in enumerate(d.strip() for d in java_decl.split(",") if d.strip()):
            tipo, _, pnombre = decl.rpartition(" ")
            visible = pnombre
            if i < len(partes_raw):
                raw = partes_raw[i]
                visible = _nombre_visible(raw if ":" in raw else (raw.split()[-1] if raw.split() else raw))
            parametros.append({"nombre": pnombre, "tipo": tipo, "nombre_visible": visible})
        metodos.append({"nombre": nombre, "nombre_visible": _nombre_visible(nombre_raw),
                        "retorno": retorno, "parametros": parametros})
    return metodos


def _campo_to_json(a: dict) -> str:
    """Entrada del toJson() tal como la espera el backend Spring (Jackson)."""
    n = a["nombre"]
    if a.get("es_pk"):
        return f"      if ({n}.isNotEmpty) '{n}': {n},"  # al crear, el backend asigna el UUID
    if a["base_tipo"] == "DateTime":
        if a.get("java_tipo") == "java.time.LocalDate":
            return f"      '{n}': {n}?.toIso8601String().substring(0, 10),"  # yyyy-MM-dd
        return f"      '{n}': {n}?.toIso8601String(),"
    return f"      '{n}': {n},"


def _generar_modelo_dart(clase: dict) -> str:
    pascal = clase["nombre_pascal"]
    attrs = clase["atributos"]

    pk_attr = next((a["nombre"] for a in attrs if a["es_pk"]), attrs[0]["nombre"])
    campos_decl = "\n".join(
        f"  {'@override\n  ' if a['nombre'] == 'id' else ''}final {a['tipo']} {a['nombre']};"
        for a in attrs
    )
    constructor_params = ",\n".join(
        f"    {'required ' if not a['tipo'].endswith('?') else ''}this.{a['nombre']}"
        for a in attrs
    )

    from_json_fields = []
    for a in attrs:
        n = a["nombre"]
        t = a["base_tipo"]
        if t == "int":
            from_json_fields.append(
                f"      {n}: json['{n}'] != null ? int.tryParse(json['{n}'].toString()) ?? 0 : 0,"
            )
        elif t == "double":
            from_json_fields.append(
                f"      {n}: json['{n}'] != null ? double.tryParse(json['{n}'].toString()) ?? 0.0 : 0.0,"
            )
        elif t == "bool":
            from_json_fields.append(
                f"      {n}: json['{n}'] == true || json['{n}'].toString().toLowerCase() == 'true',"
            )
        elif t == "DateTime":
            from_json_fields.append(
                f"      {n}: json['{n}'] != null ? DateTime.tryParse(json['{n}'].toString()) : null,"
            )
        else:
            from_json_fields.append(
                f"      {n}: json['{n}']?.toString() ?? '',"
            )
    from_json_body = "\n".join(from_json_fields)

    to_json_fields = []
    for a in attrs:
        n = a["nombre"]
        t = a["base_tipo"]
        to_json_fields.append(_campo_to_json(a))
    to_json_body = "\n".join(to_json_fields)

    copy_params = ",\n".join(f"    {a['tipo'].rstrip('?')}? {a['nombre']}" for a in attrs)
    copy_assignments = ",\n".join(f"      {a['nombre']}: {a['nombre']} ?? this.{a['nombre']}" for a in attrs)

    id_override = ""
    if not any(a["nombre"] == "id" for a in attrs):
        id_override = f"""
  @override
  dynamic get id => {pk_attr};
"""

    return f"""import '../core/models/base_model.dart';

class {pascal} implements BaseModel {{
{campos_decl}

  {pascal}({{
{constructor_params},
  }});{id_override}
  factory {pascal}.fromJson(Map<String, dynamic> json) {{
    return {pascal}(
{from_json_body}
    );
  }}

  @override
  Map<String, dynamic> toJson() {{
    return {{
{to_json_body}
    }};
  }}

  {pascal} copyWith({{
{copy_params},
  }}) {{
    return {pascal}(
{copy_assignments},
    );
  }}
}}
"""


def _generar_dto_dart(clase: dict) -> str:
    pascal = clase["nombre_pascal"]
    attrs = [a for a in clase["atributos"] if not a["es_pk"]]
    if not attrs:
        attrs = clase["atributos"]

    campos_decl = "\n".join(
        f"  {'@override\n  ' if a['nombre'] == 'id' else ''}final {a['tipo']} {a['nombre']};"
        for a in attrs
    )
    constructor_params = ",\n".join(
        f"    {'required ' if not a['tipo'].endswith('?') else ''}this.{a['nombre']}"
        for a in attrs
    )
    to_json_fields = []
    for a in attrs:
        n = a["nombre"]
        t = a["base_tipo"]
        to_json_fields.append(_campo_to_json(a))
    to_json_body = "\n".join(to_json_fields)

    return f"""import '../core/dto/base_dto.dart';

class Create{pascal}Dto implements BaseDto {{
{campos_decl}

  Create{pascal}Dto({{
{constructor_params},
  }});

  @override
  Map<String, dynamic> toJson() {{
    return {{
{to_json_body}
    }};
  }}
}}

class Update{pascal}Dto implements BaseDto {{
{campos_decl}

  Update{pascal}Dto({{
{constructor_params},
  }});

  @override
  Map<String, dynamic> toJson() {{
    return {{
{to_json_body}
    }};
  }}
}}
"""


def _generar_servicio_dart(clase: dict) -> str:
    pascal = clase["nombre_pascal"]
    snake = clase["nombre_snake"]
    endpoint = clase["endpoint"]

    return f"""import '../core/services/base_crud_service.dart';
import '../models/{snake}.dart';

class {pascal}Service extends BaseCrudService<{pascal}> {{
  {pascal}Service({{super.client}})
      : super(
          endpoint: '{endpoint}',
          fromJson: {pascal}.fromJson,
        );
}}
"""


def _obtener_meta_entidad(nombre_raw: str) -> dict:
    n = nombre_raw.lower().strip()
    if any(k in n for k in ["estudiante", "alumno"]):
        return {"icon": "Icons.school_rounded", "color": "0xFF10B981", "desc": "Expedientes, legajos y matrículas de alumnos", "badge": "Académico"}
    if any(k in n for k in ["docente", "profesor"]):
        return {"icon": "Icons.badge_rounded", "color": "0xFF3B82F6", "desc": "Cuerpo docente, especialidades y departamentos", "badge": "Personal"}
    if any(k in n for k in ["materia", "asignatura"]):
        return {"icon": "Icons.menu_book_rounded", "color": "0xFF6366F1", "desc": "Plan de estudios, códigos y créditos", "badge": "Académico"}
    if "curso" in n:
        return {"icon": "Icons.class_rounded", "color": "0xFF8B5CF6", "desc": "Gestión semestral, grupos y aulas", "badge": "Cursos"}
    if "inscripcion" in n:
        return {"icon": "Icons.how_to_reg_rounded", "color": "0xFF14B8A6", "desc": "Inscripciones de estudiantes por materia", "badge": "Matrículas"}
    if any(k in n for k in ["parcial", "examen"]):
        return {"icon": "Icons.assignment_turned_in_rounded", "color": "0xFFF59E0B", "desc": "Exámenes parciales y evaluaciones", "badge": "Evaluación"}
    if any(k in n for k in ["calificacion", "nota"]):
        return {"icon": "Icons.grade_rounded", "color": "0xFFEAB308", "desc": "Registro de calificaciones y actas", "badge": "Calificaciones"}
    if any(k in n for k in ["retiro", "baja"]):
        return {"icon": "Icons.person_remove_rounded", "color": "0xFFEF4444", "desc": "Bajas y conteo de retiros por semestre", "badge": "Retiros"}
    if "semestre" in n:
        return {"icon": "Icons.date_range_rounded", "color": "0xFF06B6D4", "desc": "Periodos lectivos y semestres académicos", "badge": "Calendario"}
    if "tarea" in n:
        return {"icon": "Icons.task_alt_rounded", "color": "0xFFA855F7", "desc": "Tareas asignadas y actividades", "badge": "Actividades"}
    if "entrega" in n:
        return {"icon": "Icons.upload_file_rounded", "color": "0xFF0284C7", "desc": "Entregas y envíos de los alumnos", "badge": "Entregas"}
    if "revision" in n:
        return {"icon": "Icons.fact_check_rounded", "color": "0xFFF97316", "desc": "Revisiones docentes y correcciones", "badge": "Docencia"}
    if "carrera" in n:
        return {"icon": "Icons.account_balance_rounded", "color": "0xFF2563EB", "desc": "Carreras universitarias y facultades", "badge": "Facultad"}
    if "horario" in n:
        return {"icon": "Icons.access_time_filled_rounded", "color": "0xFF64748B", "desc": "Distribución horaria y turnos", "badge": "Horarios"}
    if any(k in n for k in ["usuario", "user"]):
        return {"icon": "Icons.person_rounded", "color": "0xFF475569", "desc": "Cuentas de acceso y credenciales", "badge": "Seguridad"}
    if any(k in n for k in ["notificacion", "aviso"]):
        return {"icon": "Icons.notifications_active_rounded", "color": "0xFFF43F5E", "desc": "Centro de notificaciones y avisos", "badge": "Avisos"}
    if any(k in n for k in ["comentario", "feedback"]):
        return {"icon": "Icons.chat_bubble_rounded", "color": "0xFF0EA5E9", "desc": "Observaciones y retroalimentación", "badge": "Interacción"}

    if any(k in n for k in ["producto", "articulo", "item"]):
        return {"icon": "Icons.shopping_bag_rounded", "color": "0xFF10B981", "desc": "Catálogo de productos e inventario", "badge": "Catálogo"}
    if any(k in n for k in ["pedido", "orden"]):
        return {"icon": "Icons.shopping_cart_rounded", "color": "0xFF3B82F6", "desc": "Pedidos y despachos", "badge": "Ventas"}
    if any(k in n for k in ["factura", "recibo", "boleta"]):
        return {"icon": "Icons.receipt_long_rounded", "color": "0xFFF59E0B", "desc": "Emisión y cobro de facturas", "badge": "Facturación"}
    if any(k in n for k in ["cliente"]):
        return {"icon": "Icons.people_alt_rounded", "color": "0xFF6366F1", "desc": "Registro y fidelización de clientes", "badge": "Clientes"}

    if any(k in n for k in ["paciente"]):
        return {"icon": "Icons.personal_injury_rounded", "color": "0xFF10B981", "desc": "Fichas y expedientes de pacientes", "badge": "Pacientes"}
    if any(k in n for k in ["medico", "doctor"]):
        return {"icon": "Icons.medical_services_rounded", "color": "0xFF3B82F6", "desc": "Especialistas y personal de salud", "badge": "Médicos"}
    if any(k in n for k in ["cita", "consulta"]):
        return {"icon": "Icons.event_available_rounded", "color": "0xFFF59E0B", "desc": "Agenda médica y turnos", "badge": "Citas"}

    return {"icon": "Icons.dashboard_customize_rounded", "color": "0xFF38BDF8", "desc": f"Operaciones y datos de {nombre_raw}", "badge": "Gestión"}


def _analizar_dominio_proyecto(clases: List[dict], app_name: str = "") -> Tuple[str, str, str, List[dict]]:
    nombres = " ".join(c["nombre_snake"] for c in clases).lower()

    if any(k in nombres for k in ["estudiante", "docente", "materia", "parcial", "calificacion", "semestre", "carrera"]):
        titulo = "Portal Académico Universitario"
        subtitulo = "Gestión Integral de Materias, Parciales, Notas y Retiros"
        icono_hero = "Icons.account_balance_rounded"
        grupos_def = [
            {"titulo": "Gestión Académica", "icono": "Icons.school_rounded", "color": "0xFF3B82F6", "keys": ["carrera", "materia", "curso", "semestreacademico", "semestre", "horario", "aula"]},
            {"titulo": "Alumnos e Inscripciones", "icono": "Icons.how_to_reg_rounded", "color": "0xFF10B981", "keys": ["estudiante", "alumno", "inscripcion", "retiro"]},
            {"titulo": "Evaluaciones y Calificaciones", "icono": "Icons.fact_check_rounded", "color": "0xFFF59E0B", "keys": ["parcial", "parciales", "calificacion", "calificaciones", "tarea", "entrega", "revision"]},
            {"titulo": "Personal y Comunidad", "icono": "Icons.people_alt_rounded", "color": "0xFF8B5CF6", "keys": ["docente", "usuario", "notificacion", "comentario"]},
        ]
    elif any(k in nombres for k in ["producto", "pedido", "orden", "carrito", "factura", "cliente"]):
        titulo = "Plataforma Comercial y Ventas"
        subtitulo = "Catálogo de Productos, Gestión de Pedidos y Facturación"
        icono_hero = "Icons.storefront_rounded"
        grupos_def = [
            {"titulo": "Catálogo y Productos", "icono": "Icons.shopping_bag_rounded", "color": "0xFF10B981", "keys": ["producto", "categoria", "inventario"]},
            {"titulo": "Ventas y Pedidos", "icono": "Icons.shopping_cart_rounded", "color": "0xFF3B82F6", "keys": ["pedido", "orden", "carrito", "detalle_pedido"]},
            {"titulo": "Facturación y Pagos", "icono": "Icons.receipt_long_rounded", "color": "0xFFF59E0B", "keys": ["factura", "pago"]},
            {"titulo": "Clientes y Proveedores", "icono": "Icons.people_alt_rounded", "color": "0xFF8B5CF6", "keys": ["cliente", "proveedor", "usuario"]},
        ]
    elif any(k in nombres for k in ["paciente", "medico", "cita", "consulta", "historial"]):
        titulo = "Sistema Clínico y Hospitalario"
        subtitulo = "Control de Pacientes, Citas Médicas y Consultas"
        icono_hero = "Icons.local_hospital_rounded"
        grupos_def = [
            {"titulo": "Atención Médica", "icono": "Icons.event_available_rounded", "color": "0xFFF59E0B", "keys": ["cita", "consulta", "diagnostico"]},
            {"titulo": "Pacientes y Expedientes", "icono": "Icons.personal_injury_rounded", "color": "0xFF10B981", "keys": ["paciente", "historial"]},
            {"titulo": "Farmacia y Recetas", "icono": "Icons.medication_rounded", "color": "0xFF06B6D4", "keys": ["receta", "medicamento"]},
            {"titulo": "Personal de Salud", "icono": "Icons.medical_services_rounded", "color": "0xFF3B82F6", "keys": ["medico", "especialidad", "usuario"]},
        ]
    else:
        clean_title = app_name.replace("_", " ").replace("-", " ").title() or "Gestión Empresarial"
        titulo = f"Portal {clean_title}"
        subtitulo = "Módulos de Negocio sincronizados con API REST"
        icono_hero = "Icons.space_dashboard_rounded"
        mitad = max(1, len(clases) // 2)
        grupos_def = [
            {"titulo": "Módulos Principales", "icono": "Icons.category_rounded", "color": "0xFF3B82F6", "keys": [c["nombre_snake"] for c in clases[:mitad]]},
            {"titulo": "Operaciones y Registros", "icono": "Icons.view_list_rounded", "color": "0xFF10B981", "keys": [c["nombre_snake"] for c in clases[mitad:]]},
        ]

    asignadas = set()
    grupos_resultado = []
    for g in grupos_def:
        g_clases = [c for c in clases if any(k == c["nombre_snake"] for k in g["keys"]) and c["nombre_snake"] not in asignadas]
        if g_clases:
            for c in g_clases:
                asignadas.add(c["nombre_snake"])
            grupos_resultado.append({
                "titulo": g["titulo"],
                "icono": g["icono"],
                "color": g["color"],
                "clases": g_clases
            })

    restantes = [c for c in clases if c["nombre_snake"] not in asignadas]
    if restantes:
        grupos_resultado.append({
            "titulo": "Módulos Adicionales",
            "icono": "Icons.more_horiz_rounded",
            "color": "0xFF64748B",
            "clases": restantes
        })

    return titulo, subtitulo, icono_hero, grupos_resultado


# Lo que NO se copia de la plantilla nativa: código Dart viejo y basura de compilación local.
_OMITIR_PLANTILLA = {"lib", "build", ".dart_tool", ".gradle", ".idea"}
_OMITIR_ARCHIVOS = {"local.properties", ".flutter-plugins", ".flutter-plugins-dependencies", "pubspec.lock"}


def _archivos_plantilla_nativa():
    """(ruta absoluta, ruta relativa) de android/, web/, etc. de templates/flutter_skeleton."""
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "flutter_skeleton")
    if not os.path.isdir(template_dir):
        return
    for root, dirs, files in os.walk(template_dir):
        dirs[:] = [d for d in dirs if d not in _OMITIR_PLANTILLA]
        for file in files:
            if file in _OMITIR_ARCHIVOS or file.endswith(".iml"):
                continue
            abs_path = os.path.join(root, file)
            yield abs_path, os.path.relpath(abs_path, template_dir).replace("\\", "/")


def generar_app_flutter_completa(
    diagram_json: dict,
    output_dir: str,
    app_name: str = "app_movil",
    api_base_url: str = "http://localhost:8080"
) -> Dict[str, str]:
    """
    Genera la app Flutter completa a partir del diagrama:
    - Esqueleto (pubspec, .env, ApiClient, servicios base)
    - Modelos, DTOs y servicios HTTP por clase (mismos nombres/rutas que el backend Spring)
    - Interfaz de APP: splash, inicio con resumen, módulos, ajustes, lista con búsqueda,
      detalle, formularios tipados, acciones de negocio (métodos del diagrama) y animaciones.
    """
    archivos = construir_archivos_esqueleto(app_name, api_base_url)
    clases = _extraer_clases_diagrama(diagram_json)

    for c in clases:
        snake = c["nombre_snake"]
        archivos[f"lib/models/{snake}.dart"] = _generar_modelo_dart(c)
        archivos[f"lib/dto/{snake}_dto.dart"] = _generar_dto_dart(c)
        archivos[f"lib/services/{snake}_service.dart"] = _generar_servicio_dart(c)

    titulo, subtitulo, icono_hero, _ = _analizar_dominio_proyecto(clases, app_name)
    if titulo.startswith("Portal "):
        titulo = app_name.replace("_", " ").replace("-", " ").strip().title() or titulo
    entidades = [preparar_entidad(c, _obtener_meta_entidad(c["nombre_snake"].replace("_", ""))) for c in clases]
    archivos.update(archivos_interfaz(entidades, titulo, subtitulo, icono_hero))

    if output_dir:
        for abs_path, rel in _archivos_plantilla_nativa():
            if rel in archivos:
                continue
            destino = os.path.join(output_dir, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.copy2(abs_path, destino)

        for rel_path, content in archivos.items():
            full_path = os.path.join(output_dir, rel_path.replace("/", os.sep))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    return archivos


def crear_zip_app_flutter(
    diagram_json: dict,
    app_name: str = "app_movil",
    api_base_url: str = "http://10.0.2.2:8080/api"
) -> bytes:
    """
    Genera en memoria un archivo ZIP completo con el esqueleto funcional
    y todas las pantallas/modelos/servicios Flutter derivados del UML.
    """
    archivos = generar_app_flutter_completa(
        diagram_json=diagram_json,
        output_dir="",
        app_name=app_name,
        api_base_url=api_base_url
    )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Plataformas nativas (android, web, windows…) sin el lib/ viejo ni basura de compilación
        for abs_path, rel in _archivos_plantilla_nativa():
            if rel not in archivos:
                with open(abs_path, "rb") as f:
                    zf.writestr(f"{app_name}/{rel}", f.read())

        # 2. Código Dart y configuración generados
        for rel_path, content in archivos.items():
            zf.writestr(f"{app_name}/{rel_path}", content.encode("utf-8"))

    return zip_buffer.getvalue()
