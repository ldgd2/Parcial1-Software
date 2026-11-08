import 'package:movil/core/network/api_provider.dart';
import 'package:movil/modules/proyectos/models/proyecto_model.dart';
import 'package:movil/modules/proyectos/services/proyectos_endpoints.dart';

class ProyectosService {
  final ApiProvider _api;

  ProyectosService({ApiProvider? apiProvider}) : _api = apiProvider ?? api;

  Future<List<ProyectoModel>> listarMisProyectos() async {
    final Map<int, ProyectoModel> proyectosMap = {};

    // 1. Intentar obtener mis proyectos
    try {
      final responseMis = await _api.get(ProyectosEndpoints.misProyectos);
      if (responseMis is List) {
        for (final item in responseMis) {
          final p = ProyectoModel.fromJson(item as Map<String, dynamic>);
          proyectosMap[p.id] = p;
        }
      }
    } catch (_) {}

    // 2. Solo si no hay proyectos o para complementar en backend local
    if (proyectosMap.isEmpty) {
      try {
        final responseTodos = await _api.get('/proyectos/todos');
        if (responseTodos is List) {
          for (final item in responseTodos) {
            final p = ProyectoModel.fromJson(item as Map<String, dynamic>);
            if (!proyectosMap.containsKey(p.id)) {
              proyectosMap[p.id] = p;
            }
          }
        }
      } catch (_) {}
    }

    return proyectosMap.values.toList();
  }

  Future<UnirseSalaModel> unirsePorCodigo(String codigo) async {
    final cleanCode = codigo.trim();
    final response = await _api.get(ProyectosEndpoints.unirseSala(cleanCode));
    return UnirseSalaModel.fromJson(response as Map<String, dynamic>);
  }
}
