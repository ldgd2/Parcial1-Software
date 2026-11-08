import 'package:movil/core/network/api_provider.dart';
import 'package:movil/modules/visor/models/lienzo_model.dart';
import 'package:movil/modules/visor/services/visor_endpoints.dart';

class VisorService {
  final ApiProvider _api;

  VisorService({ApiProvider? apiProvider}) : _api = apiProvider ?? api;

  Future<LienzoDataModel> cargarLienzo(int proyectoId) async {
    final List<NodoModel> nodosTotales = [];
    final List<RelacionModel> relacionesTotales = [];
    final Set<String> nodeIds = {};
    final Set<String> relationIds = {};

    // 1. Consultar lienzo_json principal
    try {
      final response = await _api.get(VisorEndpoints.lienzo(proyectoId));
      if (response is Map<String, dynamic>) {
        final rawLienzo = response['lienzo_json']?.toString();
        final data = LienzoDataModel.fromRawJson(rawLienzo);
        for (final n in data.nodes) {
          if (!nodeIds.contains(n.id)) {
            nodeIds.add(n.id);
            nodosTotales.add(n);
          }
        }
        for (final r in data.relations) {
          if (!relationIds.contains(r.id)) {
            relationIds.add(r.id);
            relacionesTotales.add(r);
          }
        }
      }
    } catch (_) {}

    // 2. Si no hay elementos o para asegurar persistencia completa de DB
    if (nodosTotales.isEmpty) {
      try {
        final elResponse = await _api.get('/modelado/elementos/proyecto/$proyectoId');
        if (elResponse is List) {
          for (final item in elResponse) {
            final n = NodoModel.fromJson(item as Map<String, dynamic>);
            if (!nodeIds.contains(n.id)) {
              nodeIds.add(n.id);
              nodosTotales.add(n);
            }
          }
        }
      } catch (_) {}

      try {
        final relResponse = await _api.get('/modelado/relaciones/proyecto/$proyectoId');
        if (relResponse is List) {
          for (final item in relResponse) {
            final r = RelacionModel.fromJson(item as Map<String, dynamic>);
            if (!relationIds.contains(r.id)) {
              relationIds.add(r.id);
              relacionesTotales.add(r);
            }
          }
        }
      } catch (_) {}
    }

    return LienzoDataModel(nodes: nodosTotales, relations: relacionesTotales);
  }

  Future<List<TareaVisorModel>> cargarTareas(int proyectoId) async {
    try {
      final response = await _api.get(VisorEndpoints.tareas(proyectoId));
      if (response is List) {
        return response
            .map((t) => TareaVisorModel.fromJson(t as Map<String, dynamic>))
            .toList();
      }
    } catch (_) {}
    return [];
  }

  Future<List<RolVisorModel>> cargarRoles(int proyectoId) async {
    try {
      final response = await _api.get(VisorEndpoints.roles(proyectoId));
      if (response is List) {
        return response
            .map((r) => RolVisorModel.fromJson(r as Map<String, dynamic>))
            .toList();
      }
    } catch (_) {}
    return [];
  }
}
