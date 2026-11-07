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
    campos_decl = "\n".join(f"  final {a['tipo']} {a['nombre']};" for a in attrs)
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

    return f"""import '../core/models/base_model.dart';

class {pascal} implements BaseModel {{
{campos_decl}

  {pascal}({{
{constructor_params},
  }});

  @override
  dynamic get id => {pk_attr};

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

    campos_decl = "\n".join(f"  final {a['tipo']} {a['nombre']};" for a in attrs)
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
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualizar',
            onPressed: _refresh,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: Theme.of(context).primaryColor,
        child: const Icon(Icons.add, color: Colors.white),
        onPressed: () async {{
          final created = await Navigator.push<bool>(
            context,
            MaterialPageRoute(builder: (_) => const {pascal}FormView()),
          );
          if (created == true) _refresh();
        }},
      ),
      body: RefreshIndicator(
        onRefresh: () async => _refresh(),
        child: FutureBuilder<List<{pascal}>>(
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

            final items = snapshot.data ?? [];
            if (items.isEmpty) {{
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

            return ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8),
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
            );
          }},
        ),
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

            keyboard = "TextInputType.number" if t in ["int", "double"] else "TextInputType.text"
            widget_fields.append(f"""
            AppTextField(
              controller: _{n}Ctrl,
              label: '{_to_pascal_case(n)}',
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


def _generar_home_view_dart(clases: List[dict]) -> str:
    cards = []
    for c in clases:
        pascal = c["nombre_pascal"]
        snake = c["nombre_snake"]
        cards.append(f"""
          Card(
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const {pascal}ListView()),
              ),
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    CircleAvatar(
                      radius: 22,
                      backgroundColor: Theme.of(context).primaryColor.withOpacity(0.15),
                      child: Icon(Icons.folder_open, color: Theme.of(context).primaryColor),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '{pascal}',
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'Módulo de operaciones REST',
                          style: TextStyle(color: Colors.grey, fontSize: 12),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          )""")

    cards_code = ",\n".join(cards) if cards else """
          const Center(
            child: Text('No hay entidades UML en este proyecto.'),
          )"""

    imports = "\n".join(f"import '../{c['nombre_snake']}/{c['nombre_snake']}_list_view.dart';" for c in clases)

    return f"""import 'package:flutter/material.dart';
{imports}

class HomeView extends StatelessWidget {{
  const HomeView({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('Panel de Gestión'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 4, vertical: 8),
              child: Text(
                'Módulos del Sistema',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                crossAxisSpacing: 14,
                mainAxisSpacing: 14,
                children: [
{cards_code}
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }}
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

    archivos["lib/views/home/home_view.dart"] = _generar_home_view_dart(clases)
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
        for rel_path, content in archivos.items():
            zf.writestr(f"{app_name}/{rel_path}", content.encode("utf-8"))

    return zip_buffer.getvalue()

