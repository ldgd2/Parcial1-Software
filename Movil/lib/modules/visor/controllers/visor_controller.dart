import 'package:flutter/material.dart';
import 'package:movil/modules/visor/models/lienzo_model.dart';
import 'package:movil/modules/visor/services/visor_service.dart';
import 'package:movil/modules/visor/services/visor_websocket.dart';

class VisorController extends ChangeNotifier {
  final VisorService _service;

  VisorController({VisorService? service})
      : _service = service ?? VisorService();

  bool _isLoading = false;
  String? _errorMessage;
  LienzoDataModel _lienzoData = const LienzoDataModel(nodes: [], relations: []);
  List<TareaVisorModel> _tareas = [];
  List<RolVisorModel> _roles = [];
  final List<RevisionNotificacionModel> _notificaciones = [];
  NodoModel? _selectedNodo;
  VisorWebSocket? _ws;
  int? _currentProyectoId;

  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  LienzoDataModel get lienzoData => _lienzoData;
  List<TareaVisorModel> get tareas => _tareas;
  List<RolVisorModel> get roles => _roles;
  List<RevisionNotificacionModel> get notificaciones => List.unmodifiable(_notificaciones);
  NodoModel? get selectedNodo => _selectedNodo;
  bool get wsConectado => _ws?.estaConectado ?? false;

  void seleccionarNodo(NodoModel? nodo) {
    _selectedNodo = nodo;
    notifyListeners();
  }

  void iniciarWebSocket({
    required String codigoAcceso,
    required int proyectoId,
    required String nickname,
  }) {
    _currentProyectoId = proyectoId;
    _ws?.desconectar();

    _ws = VisorWebSocket(
      codigoAcceso: codigoAcceso,
      guestId: 'mob_${DateTime.now().millisecondsSinceEpoch}',
      nickname: nickname,
      onDiagramEvent: (event) => _procesarDiagramEvent(event, proyectoId),
      onCanvasRefresh: () => recargarLienzoSilencioso(proyectoId),
    );

    _ws!.conectar();
  }

  void _procesarDiagramEvent(Map<String, dynamic> event, int proyectoId) {
    final action = event['action']?.toString();
    final p = (event['payload'] is Map<String, dynamic>)
        ? event['payload'] as Map<String, dynamic>
        : event;

    if (action == 'moveNode') {
      final nodeId = p['id']?.toString() ?? p['nodeId']?.toString() ?? event['nodeId']?.toString();
      final x = (p['x'] as num?)?.toDouble() ?? (event['x'] as num?)?.toDouble();
      final y = (p['y'] as num?)?.toDouble() ?? (event['y'] as num?)?.toDouble();

      if (nodeId != null && x != null && y != null) {
        final nuevosNodos = _lienzoData.nodes.map((n) {
          if (n.id == nodeId) {
            return NodoModel(
              id: n.id,
              type: n.type,
              x: x,
              y: y,
              width: n.width,
              height: n.height,
              nombre: n.nombre,
              color: n.color,
              atributos: n.atributos,
              metodos: n.metodos,
              responsable: n.responsable,
              responsabilidades: n.responsabilidades,
              contenido: n.contenido,
              valores: n.valores,
              estereotipo: n.estereotipo,
              version: n.version,
            );
          }
          return n;
        }).toList();

        _lienzoData = LienzoDataModel(
          nodes: nuevosNodos,
          relations: _lienzoData.relations,
        );
        notifyListeners();
        return;
      }
    }

    if (action == 'addNode') {
      final nodeRaw = (p['node'] is Map<String, dynamic>) ? p['node'] as Map<String, dynamic> : null;
      if (nodeRaw != null) {
        final nuevo = NodoModel.fromJson(nodeRaw);
        final list = List<NodoModel>.from(_lienzoData.nodes)
          ..removeWhere((n) => n.id == nuevo.id)
          ..add(nuevo);
        _lienzoData = LienzoDataModel(nodes: list, relations: _lienzoData.relations);
        notifyListeners();
        return;
      }
    }

    if (action == 'updateNode') {
      final nodeId = p['id']?.toString();
      final partial = (p['partial'] is Map<String, dynamic>) ? p['partial'] as Map<String, dynamic> : null;
      if (nodeId != null && partial != null) {
        final list = _lienzoData.nodes.map((n) {
          if (n.id == nodeId) {
            final nuevoNombre = partial['nombre']?.toString() ?? n.nombre;
            final nuevoContenido = partial['contenido']?.toString() ?? n.contenido;
            final nuevoColor = partial['color']?.toString() ?? n.color;
            final nuevaVersion = (partial['version'] as num?)?.toInt() ?? (n.version + 1);
            return NodoModel(
              id: n.id,
              type: partial['type']?.toString() ?? n.type,
              x: (partial['x'] as num?)?.toDouble() ?? n.x,
              y: (partial['y'] as num?)?.toDouble() ?? n.y,
              width: (partial['width'] as num?)?.toDouble() ?? n.width,
              height: (partial['height'] as num?)?.toDouble() ?? n.height,
              nombre: nuevoNombre,
              color: nuevoColor,
              atributos: n.atributos,
              metodos: n.metodos,
              responsable: partial['responsable']?.toString() ?? n.responsable,
              responsabilidades: n.responsabilidades,
              contenido: nuevoContenido,
              valores: n.valores,
              estereotipo: partial['estereotipo']?.toString() ?? n.estereotipo,
              version: nuevaVersion,
            );
          }
          return n;
        }).toList();
        _lienzoData = LienzoDataModel(nodes: list, relations: _lienzoData.relations);
        notifyListeners();
        return;
      }
    }

    if (action == 'deleteNode') {
      final nodeId = p['id']?.toString();
      if (nodeId != null) {
        final list = _lienzoData.nodes.where((n) => n.id != nodeId).toList();
        final rels = _lienzoData.relations.where((r) => r.sourceId != nodeId && r.targetId != nodeId).toList();
        _lienzoData = LienzoDataModel(nodes: list, relations: rels);
        notifyListeners();
        return;
      }
    }

    if (action == 'addRelation') {
      final relRaw = (p['relation'] is Map<String, dynamic>) ? p['relation'] as Map<String, dynamic> : null;
      if (relRaw != null) {
        final nueva = RelacionModel.fromJson(relRaw);
        final list = List<RelacionModel>.from(_lienzoData.relations)
          ..removeWhere((r) => r.id == nueva.id)
          ..add(nueva);
        _lienzoData = LienzoDataModel(nodes: _lienzoData.nodes, relations: list);
        notifyListeners();
        return;
      }
    }

    if (action == 'deleteRelation') {
      final relId = p['id']?.toString();
      if (relId != null) {
        final list = _lienzoData.relations.where((r) => r.id != relId).toList();
        _lienzoData = LienzoDataModel(nodes: _lienzoData.nodes, relations: list);
        notifyListeners();
        return;
      }
    }

    // Para cualquier otra acción o sincronización CAS, recargar silencioso
    recargarLienzoSilencioso(proyectoId);
  }

  Future<void> recargarLienzoSilencioso(int proyectoId) async {
    try {
      final lienzo = await _service.cargarLienzo(proyectoId);
      if (lienzo.nodes.isNotEmpty || _lienzoData.nodes.isNotEmpty) {
        _lienzoData = lienzo;
      }
      _tareas = await _service.cargarTareas(proyectoId);
      _roles = await _service.cargarRoles(proyectoId);
      _generarNotificacionesActividad();
      notifyListeners();
    } catch (_) {}
  }

  Future<void> cargarDatos(int proyectoId, {String? lienzoInicial}) async {
    _isLoading = true;
    _errorMessage = null;

    if (lienzoInicial != null && lienzoInicial.isNotEmpty) {
      _lienzoData = LienzoDataModel.fromRawJson(lienzoInicial);
    }
    notifyListeners();

    try {
      final lienzo = await _service.cargarLienzo(proyectoId);
      if (lienzo.nodes.isNotEmpty || _lienzoData.nodes.isEmpty) {
        _lienzoData = lienzo;
      }

      _tareas = await _service.cargarTareas(proyectoId);
      _roles = await _service.cargarRoles(proyectoId);

      _generarNotificacionesActividad();

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _isLoading = false;
      if (_lienzoData.nodes.isEmpty) {
        _errorMessage = e.toString().replaceAll('Exception: ', '');
      }
      notifyListeners();
    }
  }

  void _generarNotificacionesActividad() {
    _notificaciones.clear();

    for (final rol in _roles) {
      _notificaciones.add(
        RevisionNotificacionModel(
          id: 'rol_${rol.usuarioId}',
          tipo: 'rol',
          titulo: rol.rolAsignado,
          detalle: '${rol.usuarioNombre} • ${(rol.scoreAdecuacion * 100).toInt()}% match',
          fecha: DateTime.now(),
          autor: 'Gestión Asistida',
        ),
      );
    }

    for (final tarea in _tareas) {
      _notificaciones.add(
        RevisionNotificacionModel(
          id: 'tarea_${tarea.id}',
          tipo: 'tarea',
          titulo: tarea.titulo,
          detalle: '${tarea.estado.toUpperCase()} • ${tarea.colaboradorNombre ?? 'Sin asignar'}',
          fecha: DateTime.now(),
          autor: tarea.colaboradorNombre ?? 'Sistema',
        ),
      );
    }
  }

  @override
  void dispose() {
    _ws?.desconectar();
    super.dispose();
  }
}
