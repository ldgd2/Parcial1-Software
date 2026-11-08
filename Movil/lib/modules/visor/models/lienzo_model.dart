import 'dart:convert';

class AtributoModel {
  final String id;
  final String visibilidad;
  final String nombre;
  final String tipo;

  const AtributoModel({
    required this.id,
    required this.visibilidad,
    required this.nombre,
    required this.tipo,
  });

  factory AtributoModel.fromJson(Map<String, dynamic> json) {
    return AtributoModel(
      id: json['id']?.toString() ?? '',
      visibilidad: json['visibilidad']?.toString() ?? '+',
      nombre: json['nombre']?.toString() ?? '',
      tipo: json['tipo']?.toString() ?? 'String',
    );
  }
}

class MetodoModel {
  final String id;
  final String visibilidad;
  final String nombre;
  final String parametros;
  final String retorno;

  const MetodoModel({
    required this.id,
    required this.visibilidad,
    required this.nombre,
    required this.parametros,
    required this.retorno,
  });

  factory MetodoModel.fromJson(Map<String, dynamic> json) {
    return MetodoModel(
      id: json['id']?.toString() ?? '',
      visibilidad: json['visibilidad']?.toString() ?? '+',
      nombre: json['nombre']?.toString() ?? '',
      parametros: json['parametros']?.toString() ?? '',
      retorno: json['retorno']?.toString() ?? 'void',
    );
  }
}

class NodoModel {
  final String id;
  final String type;
  final double x;
  final double y;
  final double width;
  final double height;
  final String nombre;
  final String color;
  final List<AtributoModel> atributos;
  final List<MetodoModel> metodos;
  final String? responsable;
  final List<String> responsabilidades;
  final String? contenido;
  final List<String> valores;
  final String? estereotipo;
  final int version;

  const NodoModel({
    required this.id,
    required this.type,
    required this.x,
    required this.y,
    this.width = 220,
    this.height = 180,
    required this.nombre,
    required this.color,
    required this.atributos,
    required this.metodos,
    this.responsable,
    this.responsabilidades = const [],
    this.contenido,
    this.valores = const [],
    this.estereotipo,
    this.version = 0,
  });

  factory NodoModel.fromJson(Map<String, dynamic> json) {
    final content = json['content'] is Map<String, dynamic>
        ? json['content'] as Map<String, dynamic>
        : <String, dynamic>{};

    final rawType = json['type']?.toString() ??
        content['type']?.toString() ??
        json['tipo']?.toString() ??
        'class';

    var rawAttrs = (json['atributos'] as List?) ?? (content['atributos'] as List?) ?? [];
    var attrs = rawAttrs.map((a) => AtributoModel.fromJson(a as Map<String, dynamic>)).toList();

    var rawMets = (json['metodos'] as List?) ?? (content['metodos'] as List?) ?? [];
    var mets = rawMets.map((m) => MetodoModel.fromJson(m as Map<String, dynamic>)).toList();

    var rawResp = (json['responsabilidades'] as List?) ?? (content['responsabilidades'] as List?) ?? [];
    var resps = rawResp.map((r) => r.toString()).toList();

    var rawVals = (json['valores'] as List?) ?? (content['valores'] as List?) ?? [];
    var vals = rawVals.map((v) => v.toString()).toList();

    final String? noteText = json['contenido']?.toString() ??
        content['contenido']?.toString() ??
        content['texto']?.toString() ??
        json['texto']?.toString();

    final String? resp = json['responsable']?.toString() ?? content['responsable']?.toString();
    final String? ester = json['estereotipo']?.toString() ?? content['estereotipo']?.toString();
    final String rawNombre = json['nombre']?.toString() ?? content['nombre']?.toString() ?? 'Clase';

    double defaultWidth = 220.0;
    double defaultHeight = 180.0;
    final tLower = rawType.toLowerCase();
    if (tLower == 'port') {
      defaultWidth = 28.0;
      defaultHeight = 28.0;
    } else if (tLower == 'expose_interface') {
      defaultWidth = 32.0;
      defaultHeight = 32.0;
    } else if (tLower == 'create_event' || tLower == 'destroy_event') {
      defaultWidth = 42.0;
      defaultHeight = 42.0;
    } else if (tLower == 'part') {
      defaultWidth = 190.0;
      defaultHeight = 56.0;
    } else if (tLower == 'boundary') {
      defaultWidth = 320.0;
      defaultHeight = 220.0;
    } else if (tLower == 'constraint' || tLower == 'text') {
      defaultWidth = 180.0;
      defaultHeight = 65.0;
    } else if (tLower == 'note') {
      defaultWidth = 200.0;
      defaultHeight = 90.0;
    }

    final double width = (json['width'] as num?)?.toDouble() ?? defaultWidth;
    final double height = (json['height'] as num?)?.toDouble() ?? defaultHeight;

    return NodoModel(
      id: json['id']?.toString() ?? '',
      type: rawType,
      x: (json['x'] as num?)?.toDouble() ?? (json['pos_x'] as num?)?.toDouble() ?? 50.0,
      y: (json['y'] as num?)?.toDouble() ?? (json['pos_y'] as num?)?.toDouble() ?? 50.0,
      width: width,
      height: height,
      nombre: rawNombre,
      color: json['color']?.toString() ?? '#393E46',
      atributos: attrs,
      metodos: mets,
      responsable: resp,
      responsabilidades: resps,
      contenido: noteText,
      valores: vals,
      estereotipo: ester,
      version: (json['version'] as num?)?.toInt() ?? 0,
    );
  }
}

class RelacionModel {
  final String id;
  final String type;
  final String sourceId;
  final String targetId;
  final String? label;
  final String? sourceMultiplicity;
  final String? targetMultiplicity;

  const RelacionModel({
    required this.id,
    required this.type,
    required this.sourceId,
    required this.targetId,
    this.label,
    this.sourceMultiplicity,
    this.targetMultiplicity,
  });

  factory RelacionModel.fromJson(Map<String, dynamic> json) {
    return RelacionModel(
      id: json['id']?.toString() ?? '',
      type: json['type']?.toString() ?? 'association',
      sourceId: json['sourceId']?.toString() ?? json['source_id']?.toString() ?? '',
      targetId: json['targetId']?.toString() ?? json['target_id']?.toString() ?? '',
      label: json['label']?.toString(),
      sourceMultiplicity: json['sourceMultiplicity']?.toString() ?? json['source_label']?.toString() ?? json['origen_mult']?.toString(),
      targetMultiplicity: json['targetMultiplicity']?.toString() ?? json['target_label']?.toString() ?? json['destino_mult']?.toString(),
    );
  }
}

class LienzoDataModel {
  final List<NodoModel> nodes;
  final List<RelacionModel> relations;

  const LienzoDataModel({
    required this.nodes,
    required this.relations,
  });

  factory LienzoDataModel.fromRawJson(String? raw) {
    if (raw == null || raw.trim().isEmpty || raw.trim() == 'null') {
      return const LienzoDataModel(nodes: [], relations: []);
    }
    try {
      final decoded = json.decode(raw);
      if (decoded is Map<String, dynamic>) {
        final rawNodes = decoded['nodes'] as List? ?? [];
        final rawRelations = decoded['relations'] as List? ?? [];

        return LienzoDataModel(
          nodes: rawNodes.map((n) => NodoModel.fromJson(n as Map<String, dynamic>)).toList(),
          relations: rawRelations.map((r) => RelacionModel.fromJson(r as Map<String, dynamic>)).toList(),
        );
      } else if (decoded is List) {
        return LienzoDataModel(
          nodes: decoded.map((n) => NodoModel.fromJson(n as Map<String, dynamic>)).toList(),
          relations: const [],
        );
      }
    } catch (_) {}
    return const LienzoDataModel(nodes: [], relations: []);
  }
}

class TareaVisorModel {
  final int id;
  final String titulo;
  final String descripcion;
  final String rolRequerido;
  final String? colaboradorNombre;
  final String estado;
  final String? claseAsociada;

  const TareaVisorModel({
    required this.id,
    required this.titulo,
    required this.descripcion,
    required this.rolRequerido,
    this.colaboradorNombre,
    required this.estado,
    this.claseAsociada,
  });

  factory TareaVisorModel.fromJson(Map<String, dynamic> json) {
    return TareaVisorModel(
      id: json['id'] ?? 0,
      titulo: json['titulo'] ?? '',
      descripcion: json['descripcion'] ?? '',
      rolRequerido: json['rol_requerido'] ?? 'Backend Developer',
      colaboradorNombre: json['colaborador_nombre'],
      estado: json['estado'] ?? 'pendiente',
      claseAsociada: json['clase_asociada'],
    );
  }
}

class RolVisorModel {
  final int usuarioId;
  final String usuarioNombre;
  final String rolAsignado;
  final List<String> habilidades;
  final double scoreAdecuacion;

  const RolVisorModel({
    required this.usuarioId,
    required this.usuarioNombre,
    required this.rolAsignado,
    this.habilidades = const [],
    this.scoreAdecuacion = 1.0,
  });

  factory RolVisorModel.fromJson(Map<String, dynamic> json) {
    var rawHabs = json['habilidades'] as List? ?? [];
    return RolVisorModel(
      usuarioId: json['usuario_id'] ?? 0,
      usuarioNombre: json['usuario_nombre'] ?? 'Colaborador',
      rolAsignado: json['rol_asignado'] ?? 'Miembro del Equipo',
      habilidades: rawHabs.map((h) => h.toString()).toList(),
      scoreAdecuacion: (json['score_adecuacion'] as num?)?.toDouble() ?? 1.0,
    );
  }
}

class RevisionNotificacionModel {
  final String id;
  final String tipo;
  final String titulo;
  final String detalle;
  final DateTime fecha;
  final String? autor;

  const RevisionNotificacionModel({
    required this.id,
    required this.tipo,
    required this.titulo,
    required this.detalle,
    required this.fecha,
    this.autor,
  });
}
