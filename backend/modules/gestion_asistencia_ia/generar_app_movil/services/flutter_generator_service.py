import io
import os
import re
import shutil
import zipfile
from typing import Dict, List, Any, Tuple

from backend.modules.gestion_asistencia_ia.generar_app_movil.services.flutter_skeleton_service import (
    construir_archivos_esqueleto,
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


def _map_to_dart_type(tipo_uml: str) -> Tuple[str, str]:
    t = str(tipo_uml or "").lower().strip()
    if any(k in t for k in ["int", "integer", "entero", "long", "short", "bigint", "number"]):
        return "int", "int"
    if any(k in t for k in ["double", "float", "decimal", "numeric", "real"]):
        return "double", "double"
    if any(k in t for k in ["bool", "boolean", "logico", "bit"]):
        return "bool", "bool"
    if any(k in t for k in ["date", "fecha", "time", "timestamp"]):
        return "DateTime?", "DateTime"
    return "String", "String"


def _extraer_clases_diagrama(diagram_json: dict) -> List[dict]:
    nodos = diagram_json.get("nodes", []) if isinstance(diagram_json, dict) else []
    clases = []

    for nodo in nodos:
        tipo_nodo = str(nodo.get("type", "")).lower()
        if tipo_nodo in ["class", "interface", "clase"]:
            raw_nombre = str(nodo.get("nombre") or nodo.get("name") or "Entidad").strip()
            pascal = _to_pascal_case(raw_nombre)
            snake = _to_snake_case(raw_nombre)

            atributos = []
            for a in nodo.get("atributos", []):
                nombre_raw = a.get("nombre") or a.get("name") or ""
                tipo_raw = a.get("tipo") or a.get("type") or "String"
                attr_name = _to_camel_case(nombre_raw)
                dart_type, base_type = _map_to_dart_type(tipo_raw)
                atributos.append({
                    "nombre": attr_name,
                    "tipo": dart_type,
                    "base_tipo": base_type,
                    "es_pk": a.get("visibilidad") == "PK" or attr_name.lower() in ["id", "uuid", "codigo"]
                })

            if not any(a["es_pk"] for a in atributos):
                atributos.insert(0, {
                    "nombre": "id",
                    "tipo": "String",
                    "base_tipo": "String",
                    "es_pk": True
                })

            clases.append({
                "id": nodo.get("id"),
                "nombre_pascal": pascal,
                "nombre_snake": snake,
                "endpoint": f"/api/{raw_nombre.lower()}s",
                "atributos": atributos
            })

    return clases


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
        if t == "DateTime":
            to_json_fields.append(f"      '{n}': {n}?.toIso8601String(),")
        else:
            to_json_fields.append(f"      '{n}': {n},")
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
        if t == "DateTime":
            to_json_fields.append(f"      '{n}': {n}?.toIso8601String(),")
        else:
            to_json_fields.append(f"      '{n}': {n},")
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

    return f"""import '../core/network/api_client.dart';
import '../core/services/base_crud_service.dart';
import '../models/{snake}.dart';

class {pascal}Service extends BaseCrudService<{pascal}> {{
  {pascal}Service({{ApiClient? client}})
      : super(
          endpoint: '{endpoint}',
          fromJson: {pascal}.fromJson,
          client: client,
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


def _generar_list_view_dart(clase: dict) -> str:
    pascal = clase["nombre_pascal"]
    snake = clase["nombre_snake"]
    attrs = clase["atributos"]

    pk_attr = next((a["nombre"] for a in attrs if a["es_pk"]), attrs[0]["nombre"])
    display_attr = next((a["nombre"] for a in attrs if not a["es_pk"] and a["base_tipo"] == "String"), pk_attr)
    sub_attr = next((a["nombre"] for a in attrs if a["nombre"] not in [pk_attr, display_attr]), None)

    sub_expr = f"'${{item.{sub_attr}}}'" if sub_attr else f"'ID: ${{item.{pk_attr}}}'"

    return f"""import 'package:flutter/material.dart';
import '../../models/{snake}.dart';
import '../../services/{snake}_service.dart';
import '../../shared/widgets/loading_widget.dart';
import '../../shared/widgets/empty_state_widget.dart';
import '../../shared/widgets/error_state_widget.dart';
import '../../shared/widgets/confirm_dialog.dart';
import '../../shared/widgets/entity_card.dart';
import '{snake}_form_view.dart';

class {pascal}ListView extends StatefulWidget {{
  const {pascal}ListView({{super.key}});

  @override
  State<{pascal}ListView> createState() => _{pascal}ListViewState();
}}

class _{pascal}ListViewState extends State<{pascal}ListView> {{
  final {pascal}Service _service = {pascal}Service();
  late Future<List<{pascal}>> _itemsFuture;
  String _filter = '';

  @override
  void initState() {{
    super.initState();
    _refresh();
  }}

  void _refresh() {{
    setState(() {{
      _itemsFuture = _service.getAll();
    }});
  }}

  Future<void> _deleteItem(dynamic id) async {{
    final confirm = await ConfirmDialog.show(
      context: context,
      title: 'Eliminar {pascal}',
      message: '¿Estás seguro de que deseas eliminar este registro permanentemente?',
    );

    if (confirm == true) {{
      try {{
        await _service.delete(id);
        if (mounted) {{
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Registro eliminado correctamente')),
          );
          _refresh();
        }}
      }} catch (e) {{
        if (mounted) {{
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error al eliminar: $e')),
          );
        }}
      }}
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{pascal}s'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Actualizar',
            onPressed: _refresh,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: Theme.of(context).primaryColor,
        icon: const Icon(Icons.add_rounded, color: Colors.white),
        label: const Text('Nuevo', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        onPressed: () async {{
          final created = await Navigator.push<bool>(
            context,
            MaterialPageRoute(builder: (_) => const {pascal}FormView()),
          );
          if (created == true) _refresh();
        }},
      ),
      body: FutureBuilder<List<{pascal}>>(
        future: _itemsFuture,
        builder: (context, snapshot) {{
          if (snapshot.connectionState == ConnectionState.waiting) {{
            return const LoadingWidget(message: 'Cargando {pascal}s...');
          }}
          if (snapshot.hasError) {{
            return ErrorStateWidget(
              error: snapshot.error.toString(),
              onRetry: _refresh,
            );
          }}

          final allItems = snapshot.data ?? [];
          final items = _filter.trim().isEmpty
              ? allItems
              : allItems.where((it) => it.{display_attr}.toString().toLowerCase().contains(_filter.toLowerCase())).toList();

          if (allItems.isEmpty) {{
            return EmptyStateWidget(
              title: 'Sin {pascal}s',
              subtitle: 'Aún no se han registrado datos en este módulo.',
              actionLabel: 'Crear {pascal}',
              onAction: () async {{
                final created = await Navigator.push<bool>(
                  context,
                  MaterialPageRoute(builder: (_) => const {pascal}FormView()),
                );
                if (created == true) _refresh();
              }},
            );
          }}

          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
                child: TextField(
                  onChanged: (v) => setState(() => _filter = v),
                  decoration: InputDecoration(
                    hintText: 'Filtrar en {pascal}s (${{allItems.length}})...',
                    hintStyle: const TextStyle(fontSize: 13, color: Color(0xFF64748B)),
                    prefixIcon: const Icon(Icons.search_rounded, size: 20, color: Color(0xFF94A3B8)),
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: Color(0xFF334155)),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: Color(0xFF334155)),
                    ),
                  ),
                ),
              ),
              Expanded(
                child: items.isEmpty
                    ? const Center(child: Text('No hay registros coincidentes.', style: TextStyle(color: Color(0xFF94A3B8))))
                    : RefreshIndicator(
                        onRefresh: () async => _refresh(),
                        child: ListView.builder(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          itemCount: items.length,
                          itemBuilder: (context, index) {{
                            final item = items[index];
                            return EntityCard(
                              title: '${{item.{display_attr}}}',
                              subtitle: {sub_expr},
                              onTap: () async {{
                                final updated = await Navigator.push<bool>(
                                  context,
                                  MaterialPageRoute(builder: (_) => {pascal}FormView(item: item)),
                                );
                                if (updated == true) _refresh();
                              }},
                              onEdit: () async {{
                                final updated = await Navigator.push<bool>(
                                  context,
                                  MaterialPageRoute(builder: (_) => {pascal}FormView(item: item)),
                                );
                                if (updated == true) _refresh();
                              }},
                              onDelete: () => _deleteItem(item.id),
                            );
                          }},
                        ),
                      ),
              ),
            ],
          );
        }},
      ),
    );
  }}
}}
"""


def _generar_form_view_dart(clase: dict) -> str:
    pascal = clase["nombre_pascal"]
    snake = clase["nombre_snake"]
    attrs = clase["atributos"]

    pk_attr = next((a for a in attrs if a["es_pk"]), attrs[0])
    form_attrs = [a for a in attrs if a != pk_attr]

    controller_decls = []
    controller_inits = []
    controller_disposes = []
    widget_fields = []
    model_instantiations = []

    for a in form_attrs:
        n = a["nombre"]
        t = a["base_tipo"]

        if t in ["int", "double", "String"]:
            controller_decls.append(f"  late TextEditingController _{n}Ctrl;")
            controller_inits.append(
                f"    _{n}Ctrl = TextEditingController(text: widget.item?.{n}.toString() ?? '');"
            )
            controller_disposes.append(f"    _{n}Ctrl.dispose();")

            n_lower = n.lower()
            keyboard = "TextInputType.number" if t in ["int", "double"] else "TextInputType.text"
            prefix_icon_code = "Icons.edit_note_rounded"
            obscure_code = "false"
            max_lines_code = "1"

            if "email" in n_lower or "correo" in n_lower:
                keyboard = "TextInputType.emailAddress"
                prefix_icon_code = "Icons.email_outlined"
            elif "pass" in n_lower or "clave" in n_lower or "contrasena" in n_lower or "password" in n_lower:
                prefix_icon_code = "Icons.lock_outline"
                obscure_code = "true"
            elif "tel" in n_lower or "cel" in n_lower or "phone" in n_lower:
                keyboard = "TextInputType.phone"
                prefix_icon_code = "Icons.phone_outlined"
            elif "desc" in n_lower or "obs" in n_lower or "coment" in n_lower or "mensaje" in n_lower or "texto" in n_lower:
                keyboard = "TextInputType.multiline"
                prefix_icon_code = "Icons.notes_rounded"
                max_lines_code = "3"
            elif n_lower.endswith("_id") or n_lower.startswith("id_") or "fk" in n_lower:
                prefix_icon_code = "Icons.link_rounded"
            elif t in ["int", "double"]:
                prefix_icon_code = "Icons.numbers_rounded"

            label_text = _to_pascal_case(n)
            if n_lower.endswith("_id") or n_lower.startswith("id_") or "fk" in n_lower:
                label_text += " (Relación FK)"

            widget_fields.append(f"""
            AppTextField(
              controller: _{n}Ctrl,
              label: '{label_text}',
              prefixIcon: {prefix_icon_code},
              obscureText: {obscure_code},
              maxLines: {max_lines_code},
              keyboardType: {keyboard},
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Campo requerido' : null,
            ),""")

            if t == "int":
                model_instantiations.append(f"          {n}: int.tryParse(_{n}Ctrl.text.trim()) ?? 0,")
            elif t == "double":
                model_instantiations.append(f"          {n}: double.tryParse(_{n}Ctrl.text.trim()) ?? 0.0,")
            else:
                model_instantiations.append(f"          {n}: _{n}Ctrl.text.trim(),")

        elif t == "bool":
            controller_decls.append(f"  late bool _{n}Val;")
            controller_inits.append(f"    _{n}Val = widget.item?.{n} ?? false;")
            widget_fields.append(f"""
            SwitchListTile(
              title: const Text('{_to_pascal_case(n)}'),
              value: _{n}Val,
              onChanged: (v) => setState(() => _{n}Val = v),
            ),
            const SizedBox(height: 16),""")
            model_instantiations.append(f"          {n}: _{n}Val,")

        elif t == "DateTime":
            controller_decls.append(f"  DateTime? _{n}Date;")
            controller_inits.append(f"    _{n}Date = widget.item?.{n} ?? DateTime.now();")
            widget_fields.append(f"""
            ListTile(
              title: Text('Fecha: ${{_{n}Date?.toLocal().toString().split(' ')[0] ?? 'Seleccionar'}}'),
              trailing: const Icon(Icons.calendar_today),
              onTap: () async {{
                final picked = await showDatePicker(
                  context: context,
                  initialDate: _{n}Date ?? DateTime.now(),
                  firstDate: DateTime(2000),
                  lastDate: DateTime(2100),
                );
                if (picked != null) setState(() => _{n}Date = picked);
              }},
            ),
            const SizedBox(height: 16),""")
            model_instantiations.append(f"          {n}: _{n}Date,")

    decls_code = "\n".join(controller_decls)
    inits_code = "\n".join(controller_inits)
    disposes_code = "\n".join(controller_disposes)
    widgets_code = "\n".join(widget_fields)
    instantiations_code = "\n".join(model_instantiations)

    pk_type = pk_attr["base_tipo"]
    if pk_type == "int":
        pk_create_expr = "0"
    elif pk_type == "double":
        pk_create_expr = "0.0"
    else:
        pk_create_expr = "''"

    return f"""import 'package:flutter/material.dart';
import '../../models/{snake}.dart';
import '../../services/{snake}_service.dart';
import '../../shared/widgets/app_text_field.dart';
import '../../shared/widgets/app_button.dart';

class {pascal}FormView extends StatefulWidget {{
  final {pascal}? item;

  const {pascal}FormView({{super.key, this.item}});

  @override
  State<{pascal}FormView> createState() => _{pascal}FormViewState();
}}

class _{pascal}FormViewState extends State<{pascal}FormView> {{
  final _formKey = GlobalKey<FormState>();
  final {pascal}Service _service = {pascal}Service();
  bool _isLoading = false;

{decls_code}

  @override
  void initState() {{
    super.initState();
{inits_code}
  }}

  @override
  void dispose() {{
{disposes_code}
    super.dispose();
  }}

  Future<void> _save() async {{
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {{
      final isEdit = widget.item != null;
      final payload = {pascal}(
        {pk_attr['nombre']}: isEdit ? widget.item!.{pk_attr['nombre']} : {pk_create_expr},
{instantiations_code}
      );

      if (isEdit) {{
        await _service.update(widget.item!.{pk_attr['nombre']}, payload.toJson());
      }} else {{
        await _service.create(payload.toJson());
      }}

      if (mounted) {{
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(isEdit ? 'Actualizado correctamente' : 'Creado con éxito')),
        );
        Navigator.pop(context, true);
      }}
    }} catch (e) {{
      if (mounted) {{
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al guardar: $e')),
        );
      }}
    }} finally {{
      if (mounted) setState(() => _isLoading = false);
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    final isEdit = widget.item != null;

    return Scaffold(
      appBar: AppBar(
        title: Text(isEdit ? 'Editar {pascal}' : 'Nuevo {pascal}'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
{widgets_code}
              const SizedBox(height: 24),
              AppButton(
                text: isEdit ? 'Guardar Cambios' : 'Registrar {pascal}',
                isLoading: _isLoading,
                onPressed: _save,
              ),
            ],
          ),
        ),
      ),
    );
  }}
}}
"""


def _generar_home_view_dart(clases: List[dict], app_name: str = "app_movil") -> str:
    titulo_hero, subtitulo_hero, icono_hero, grupos = _analizar_dominio_proyecto(clases, app_name)

    imports = "\n".join(f"import '../{c['nombre_snake']}/{c['nombre_snake']}_list_view.dart';" for c in clases)

    rutas_cases = []
    for c in clases:
        pascal = c["nombre_pascal"]
        snake = c["nombre_snake"]
        rutas_cases.append(f"""      case '{snake}':
        Navigator.push(context, MaterialPageRoute(builder: (_) => const {pascal}ListView()));
        break;""")
    rutas_code = "\n".join(rutas_cases)

    grupos_dart = []
    for g in grupos:
        items_dart = []
        for c in g["clases"]:
            pascal = c["nombre_pascal"]
            snake = c["nombre_snake"]
            meta = _obtener_meta_entidad(pascal)
            items_dart.append(f"""              _ModuleItem(
                id: '{snake}',
                name: '{pascal}',
                desc: '{meta["desc"]}',
                badge: '{meta["badge"]}',
                icon: {meta["icon"]},
                color: const Color({meta["color"]}),
              )""")
        items_code = ",\n".join(items_dart)
        grupos_dart.append(f"""        _ModuleGroup(
          title: '{g["titulo"]}',
          icon: {g["icono"]},
          color: const Color({g["color"]}),
          items: [
{items_code}
          ],
        )""")
    grupos_code = ",\n".join(grupos_dart)

    return f"""import 'package:flutter/material.dart';
{imports}

class HomeView extends StatefulWidget {{
  const HomeView({{super.key}});

  @override
  State<HomeView> createState() => _HomeViewState();
}}

class _HomeViewState extends State<HomeView> {{
  String _searchQuery = '';

  final List<_ModuleGroup> _groups = [
{grupos_code}
  ];

  void _navigateToModule(BuildContext context, String moduleId) {{
    switch (moduleId) {{
{rutas_code}
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    final query = _searchQuery.toLowerCase().trim();

    final filteredGroups = _groups.map((group) {{
      final matchingItems = group.items.where((it) {{
        return it.name.toLowerCase().contains(query) ||
               it.desc.toLowerCase().contains(query) ||
               it.badge.toLowerCase().contains(query);
      }}).toList();
      return _ModuleGroup(
        title: group.title,
        icon: group.icon,
        color: group.color,
        items: matchingItems,
      );
    }}).where((g) => g.items.isNotEmpty).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('{titulo_hero}'),
        centerTitle: false,
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFF10B981).withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF10B981).withValues(alpha: 0.4)),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.bolt, size: 14, color: Color(0xFF10B981)),
                SizedBox(width: 4),
                Text('Persistente', style: TextStyle(color: Color(0xFF10B981), fontSize: 11, fontWeight: FontWeight.bold)),
              ],
            ),
          ),
        ],
      ),
      body: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF1E293B), Color(0xFF0F172A)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        CircleAvatar(
                          radius: 22,
                          backgroundColor: const Color(0xFF38BDF8).withValues(alpha: 0.15),
                          child: const Icon({icono_hero}, color: Color(0xFF38BDF8), size: 24),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                '{titulo_hero}',
                                style: TextStyle(
                                  color: Color(0xFFF8FAFC),
                                  fontSize: 17,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '{subtitulo_hero}',
                                style: const TextStyle(
                                  color: Color(0xFF94A3B8),
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        _buildMetricPill(Icons.layers_outlined, '{len(clases)} Módulos'),
                        const SizedBox(width: 8),
                        _buildMetricPill(Icons.sync_rounded, 'REST Sync'),
                        const SizedBox(width: 8),
                        _buildMetricPill(Icons.shield_outlined, 'Persistencia OK'),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
              child: TextField(
                onChanged: (v) => setState(() => _searchQuery = v),
                decoration: InputDecoration(
                  hintText: 'Buscar módulos, materias, notas...',
                  hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                  prefixIcon: const Icon(Icons.search, size: 20, color: Color(0xFF94A3B8)),
                  filled: true,
                  fillColor: const Color(0xFF1E293B),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: Color(0xFF334155)),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: Color(0xFF334155)),
                  ),
                ),
              ),
            ),
          ),
          if (filteredGroups.isEmpty)
            const SliverFillRemaining(
              hasScrollBody: false,
              child: Center(
                child: Text('No se encontraron módulos coincidentes con la búsqueda.'),
              ),
            )
          else
            SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, index) {{
                  final group = filteredGroups[index];
                  return Padding(
                    padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(group.icon, size: 18, color: group.color),
                            const SizedBox(width: 8),
                            Text(
                              group.title,
                              style: const TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFFF8FAFC),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                              decoration: BoxDecoration(
                                color: group.color.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                '${{group.items.length}}',
                                style: TextStyle(color: group.color, fontSize: 11, fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        ...group.items.map((item) => _buildModuleCard(context, item)),
                      ],
                    ),
                  );
                }},
                childCount: filteredGroups.length,
              ),
            ),
        ],
      ),
    );
  }}

  Widget _buildMetricPill(IconData icon, String label) {{
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: const Color(0xFF38BDF8)),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(color: Color(0xFFCBD5E1), fontSize: 11, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }}

  Widget _buildModuleCard(BuildContext context, _ModuleItem item) {{
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () => _navigateToModule(context, item.id),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 20,
                  backgroundColor: item.color.withValues(alpha: 0.15),
                  child: Icon(item.icon, color: item.color, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            item.name,
                            style: const TextStyle(
                              fontWeight: FontWeight.w700,
                              fontSize: 15,
                              color: Color(0xFFF8FAFC),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                            decoration: BoxDecoration(
                              color: item.color.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              item.badge,
                              style: TextStyle(
                                color: item.color,
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 3),
                      Text(
                        item.desc,
                        style: const TextStyle(
                          color: Color(0xFF94A3B8),
                          fontSize: 12,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                const Icon(
                  Icons.arrow_forward_ios_rounded,
                  size: 14,
                  color: Color(0xFF64748B),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }}
}}

class _ModuleGroup {{
  final String title;
  final IconData icon;
  final Color color;
  final List<_ModuleItem> items;

  _ModuleGroup({{
    required this.title,
    required this.icon,
    required this.color,
    required this.items,
  }});
}}

class _ModuleItem {{
  final String id;
  final String name;
  final String desc;
  final String badge;
  final IconData icon;
  final Color color;

  _ModuleItem({{
    required this.id,
    required this.name,
    required this.desc,
    required this.badge,
    required this.icon,
    required this.color,
  }});
}}
"""


def _generar_main_dart(app_name: str, clases: List[dict]) -> str:
    title = app_name.replace("_", " ").title()
    return f"""import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'views/home/home_view.dart';

void main() {{
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MainApp());
}}

class MainApp extends StatelessWidget {{
  const MainApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{title}',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const HomeView(),
    );
  }}
}}
"""


def generar_app_flutter_completa(
    diagram_json: dict,
    output_dir: str,
    app_name: str = "app_movil",
    api_base_url: str = "http://localhost:8080"
) -> Dict[str, str]:
    """
    Construye de forma hiper-modular, completa y determinista toda la aplicación
    móvil en Flutter:
    - Esqueleto estricto (pubspec, analysis, themes, api_client, api_config)
    - Modelos Dart por cada clase UML
    - Servicios HTTP CRUD por cada clase
    - Vistas CRUD completas (List y Form) por cada clase
    - Home dashboard de navegación
    - main.dart configurado
    """
    archivos = construir_archivos_esqueleto(app_name, api_base_url)
    clases = _extraer_clases_diagrama(diagram_json)

    for c in clases:
        snake = c["nombre_snake"]
        archivos[f"lib/models/{snake}.dart"] = _generar_modelo_dart(c)
        archivos[f"lib/dto/{snake}_dto.dart"] = _generar_dto_dart(c)
        archivos[f"lib/services/{snake}_service.dart"] = _generar_servicio_dart(c)
        archivos[f"lib/views/{snake}/{snake}_list_view.dart"] = _generar_list_view_dart(c)
        archivos[f"lib/views/{snake}/{snake}_form_view.dart"] = _generar_form_view_dart(c)

    archivos["lib/views/home/home_view.dart"] = _generar_home_view_dart(clases, app_name)
    archivos["lib/main.dart"] = _generar_main_dart(app_name, clases)

    if output_dir:
        # Copiar plantilla física previa si existe
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates",
            "flutter_skeleton"
        )
        if os.path.isdir(template_dir):
            shutil.copytree(template_dir, output_dir, dirs_exist_ok=True)

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
        # 1. Incluir estructura de plataformas nativas físicas (android, web, windows)
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates",
            "flutter_skeleton"
        )
        if os.path.isdir(template_dir):
            for root, _, files in os.walk(template_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_to_template = os.path.relpath(abs_path, template_dir).replace("\\", "/")
                    if rel_to_template not in archivos:
                        with open(abs_path, "rb") as f:
                            zf.writestr(f"{app_name}/{rel_to_template}", f.read())

        # 2. Escribir archivos autogenerados de Dart y configuración
        for rel_path, content in archivos.items():
            zf.writestr(f"{app_name}/{rel_path}", content.encode("utf-8"))

    return zip_buffer.getvalue()

