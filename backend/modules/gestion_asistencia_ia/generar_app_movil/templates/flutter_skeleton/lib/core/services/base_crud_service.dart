import '../network/api_client.dart';
import '../models/base_model.dart';

abstract class BaseCrudService<T extends BaseModel> {
  final ApiClient client;
  final String endpoint;
  final T Function(Map<String, dynamic> json) fromJson;

  BaseCrudService({
    required this.endpoint,
    required this.fromJson,
    ApiClient? client,
  }) : client = client ?? ApiClient();

  Future<List<T>> getAll() async {
    final response = await client.get(endpoint);
    if (response == null) return [];
    if (response is List) {
      return response.map((item) => fromJson(Map<String, dynamic>.from(item as Map))).toList();
    }
    if (response is Map) {
      final list = response['content'] ?? response['items'] ?? response['data'] ?? [];
      return (list as List).map((item) => fromJson(Map<String, dynamic>.from(item as Map))).toList();
    }
    return [];
  }

  Future<T> getById(dynamic id) async {
    final response = await client.get('$endpoint/$id');
    return fromJson(Map<String, dynamic>.from(response as Map));
  }

  Future<T> create(Map<String, dynamic> data) async {
    final response = await client.post(endpoint, data);
    return fromJson(Map<String, dynamic>.from(response as Map));
  }

  Future<T> update(dynamic id, Map<String, dynamic> data) async {
    final response = await client.put('$endpoint/$id', data);
    return fromJson(Map<String, dynamic>.from(response as Map));
  }

  Future<void> delete(dynamic id) async {
    await client.delete('$endpoint/$id');
  }
}

