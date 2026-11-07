import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import 'api_exception.dart';

class ApiClient {
  final String baseUrl;

  ApiClient({String? baseUrl}) : baseUrl = baseUrl ?? ApiConfig.baseUrl;

  Future<dynamic> get(String endpoint) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    final response = await http
        .get(uri, headers: ApiConfig.defaultHeaders)
        .timeout(ApiConfig.timeout);
    return _handleResponse(response);
  }

  Future<dynamic> post(String endpoint, Map<String, dynamic> body) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    final response = await http
        .post(
          uri,
          headers: ApiConfig.defaultHeaders,
          body: jsonEncode(body),
        )
        .timeout(ApiConfig.timeout);
    return _handleResponse(response);
  }

  Future<dynamic> put(String endpoint, Map<String, dynamic> body) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    final response = await http
        .put(
          uri,
          headers: ApiConfig.defaultHeaders,
          body: jsonEncode(body),
        )
        .timeout(ApiConfig.timeout);
    return _handleResponse(response);
  }

  Future<dynamic> delete(String endpoint) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    final response = await http
        .delete(uri, headers: ApiConfig.defaultHeaders)
        .timeout(ApiConfig.timeout);
    return _handleResponse(response);
  }

  dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return null;
      return jsonDecode(utf8.decode(response.bodyBytes));
    } else {
      String errorMessage = 'Error al comunicarse con el servidor';
      try {
        final errorData = jsonDecode(utf8.decode(response.bodyBytes));
        if (errorData is Map && errorData.containsKey('message')) {
          errorMessage = errorData['message'].toString();
        } else if (errorData is Map && errorData.containsKey('detail')) {
          errorMessage = errorData['detail'].toString();
        }
      } catch (_) {
        if (response.body.isNotEmpty) {
          errorMessage = response.body;
        } else {
          errorMessage = 'Código HTTP ${response.statusCode}';
        }
      }
      throw ApiException(response.statusCode, errorMessage);
    }
  }
}

