import re
import unicodedata
from typing import Dict


_PALABRAS_RESERVADAS_DART = {
    "abstract", "as", "assert", "async", "await", "base", "break", "case", "catch", "class", "const",
    "continue", "covariant", "default", "deferred", "do", "dynamic", "else", "enum", "export",
    "extends", "extension", "external", "factory", "false", "final", "finally", "for", "function",
    "get", "hide", "if", "implements", "import", "in", "interface", "is", "late", "library", "mixin",
    "new", "null", "of", "on", "operator", "part", "required", "rethrow", "return", "sealed", "set",
    "show", "static", "super", "switch", "sync", "this", "throw", "true", "try", "type", "typedef",
    "var", "void", "when", "while", "with", "yield",
}
# Un paquete no puede llamarse igual que una de sus dependencias
_PAQUETES_DEL_PUBSPEC = {"flutter", "flutter_test", "flutter_lints", "flutter_dotenv", "http", "intl"}


def nombre_paquete_dart(app_name: str) -> str:
    """Nombre válido para `name:` del pubspec, sea cual sea el nombre del repo.

    Reglas de Dart: solo minúsculas, dígitos y `_`, empezar con letra o `_` y no ser palabra
    reservada. Antes un repo llamado "6767" generaba `name: 6767` y `flutter pub get` fallaba con
    'Expected "name" to be a string, but got 6767'.
    """
    texto = unicodedata.normalize("NFKD", str(app_name or "")).encode("ascii", "ignore").decode()
    nombre = re.sub(r"_+", "_", re.sub(r"[^a-z0-9_]", "_", texto.lower())).strip("_")
    if not nombre:
        return "app_movil"
    if nombre[0].isdigit():
        nombre = f"app_{nombre}"
    if nombre in _PALABRAS_RESERVADAS_DART or nombre in _PAQUETES_DEL_PUBSPEC:
        nombre = f"{nombre}_app"
    return nombre


def generar_pubspec_yaml(app_name: str) -> str:
    safe_name = nombre_paquete_dart(app_name)
    return f"""name: {safe_name}
description: "Aplicación móvil en Flutter generada automáticamente para consumir el backend Spring Boot."
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0
  intl: ^0.19.0
  flutter_dotenv: ^5.2.1

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
  assets:
    - .env
"""


def generar_analysis_options() -> str:
    return """include: package:flutter_lints/flutter.yaml

linter:
  rules:
    prefer_const_constructors: true
    prefer_const_literals_to_create_immutables: true
    avoid_print: false
"""


def generar_flutter_gitignore() -> str:
    return """# Flutter/Dart
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.packages
build/
.pub-cache/
.pub/

# IDEs
.idea/
.vscode/
*.iml

# OS
.DS_Store
Thumbs.db
"""


def generar_readme_flutter(app_name: str, api_base_url: str) -> str:
    return f"""# {app_name.capitalize()} - Aplicación Móvil Flutter

Esta aplicación móvil fue generada automáticamente para interactuar directamente con la API REST del backend en Spring Boot.

## Requisitos
- Flutter SDK 3.0.0 o superior
- Dart 3.0.0 o superior
- Conexión al backend ({api_base_url})

## Configurar la URL de la API (`.env`)
La URL del backend NO está escrita en el código: se lee del archivo `.env` de esta carpeta.

```env
API_BASE_URL={api_base_url.rstrip("/")}
API_TIMEOUT_SECONDS=20
MONEDA=Bs
```

- `.env.example` es la plantilla: cópiala a `.env` si no existe.
- Emulador Android contra un backend en tu PC: `API_BASE_URL=http://10.0.2.2:8080`
- Celular físico en tu red: `API_BASE_URL=http://<IP-de-tu-PC>:8080`
- Después de cambiar el `.env` vuelve a ejecutar `flutter run` (es un asset: un hot reload no lo relee).
- También puedes forzarla al compilar: `flutter run --dart-define=API_BASE_URL=https://mi-api.com`

## Ejecución
```bash
flutter pub get
flutter run
```
"""


def generar_env(api_base_url: str) -> str:
    return f"""# URL base del backend Spring Boot (sin / al final). Cámbiala aquí, no en el código.
API_BASE_URL={api_base_url.rstrip("/")}
# Segundos de espera por petición
API_TIMEOUT_SECONDS=20
# Símbolo de moneda para precios y totales
MONEDA=Bs
"""


def generar_env_example() -> str:
    return """# Copia este archivo a .env y ajusta los valores.
# Backend desplegado:         https://<dominio>/host/<usuario>/<proyecto>
# Emulador Android (backend en tu PC): http://10.0.2.2:8080
# Celular físico en tu red:   http://<IP-de-tu-PC>:8080
API_BASE_URL=http://10.0.2.2:8080
API_TIMEOUT_SECONDS=20
MONEDA=Bs
"""


def generar_api_config(api_base_url: str) -> str:
    clean_url = api_base_url.rstrip("/")
    return f"""import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Configuración de la API. Los valores salen del archivo `.env` (ver README):
///   API_BASE_URL, API_TIMEOUT_SECONDS
/// Prioridad: --dart-define=API_BASE_URL  >  .env  >  valor de respaldo.
class ApiConfig {{
  static const String _urlRespaldo = '{clean_url}';
  static const String _urlCompilacion = String.fromEnvironment('API_BASE_URL');

  static String? _leer(String clave) {{
    if (!dotenv.isInitialized) return null;
    final valor = dotenv.maybeGet(clave)?.trim();
    return (valor == null || valor.isEmpty) ? null : valor;
  }}

  /// URL base del backend, sin "/" final.
  static String get baseUrl {{
    final url = _urlCompilacion.isNotEmpty ? _urlCompilacion : (_leer('API_BASE_URL') ?? _urlRespaldo);
    return url.endsWith('/') ? url.substring(0, url.length - 1) : url;
  }}

  static Duration get timeout =>
      Duration(seconds: int.tryParse(_leer('API_TIMEOUT_SECONDS') ?? '') ?? 20);

  static Map<String, String> defaultHeaders = {{
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }};
}}
"""


def generar_api_client() -> str:
    return """import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;

  ApiException(this.statusCode, this.message);

  @override
  String toString() => 'ApiException [$statusCode]: $message';
}

class ApiClient {
  final String baseUrl;

  ApiClient({String? baseUrl}) : baseUrl = baseUrl ?? ApiConfig.baseUrl;

  /// Ejecuta la petición traduciendo fallos de red a un ApiException entendible.
  Future<dynamic> _enviar(Future<http.Response> Function() peticion) async {
    try {
      final response = await peticion().timeout(ApiConfig.timeout);
      return _handleResponse(response);
    } on ApiException {
      rethrow;
    } on TimeoutException {
      throw ApiException(0, 'El servidor no respondió a tiempo ($baseUrl). Revisa API_BASE_URL en el archivo .env');
    } catch (e) {
      throw ApiException(0, 'No se pudo conectar con $baseUrl. Revisa API_BASE_URL en el archivo .env ($e)');
    }
  }

  Future<dynamic> get(String endpoint) =>
      _enviar(() => http.get(Uri.parse('$baseUrl$endpoint'), headers: ApiConfig.defaultHeaders));

  Future<dynamic> post(String endpoint, Map<String, dynamic> body) => _enviar(() => http.post(
        Uri.parse('$baseUrl$endpoint'),
        headers: ApiConfig.defaultHeaders,
        body: jsonEncode(body),
      ));

  Future<dynamic> put(String endpoint, Map<String, dynamic> body) => _enviar(() => http.put(
        Uri.parse('$baseUrl$endpoint'),
        headers: ApiConfig.defaultHeaders,
        body: jsonEncode(body),
      ));

  Future<dynamic> delete(String endpoint) =>
      _enviar(() => http.delete(Uri.parse('$baseUrl$endpoint'), headers: ApiConfig.defaultHeaders));

  dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return null;
      final texto = utf8.decode(response.bodyBytes);
      try {
        return jsonDecode(texto);
      } on FormatException {
        return texto;
      }
    } else {
      String errorMessage = 'Error al comunicarse con el servidor';
      try {
        final errorData = jsonDecode(utf8.decode(response.bodyBytes));
        if (errorData is Map && errorData['errors'] is Map) {
          errorMessage = (errorData['errors'] as Map).values.join(', ');
        } else if (errorData is Map && errorData.containsKey('message')) {
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
"""


def generar_base_model() -> str:
    return """abstract class BaseModel {
  dynamic get id;
  Map<String, dynamic> toJson();
}
"""


def generar_base_dto() -> str:
    return """abstract class BaseDto {
  Map<String, dynamic> toJson();
}

class ApiResponse<T> {
  final bool success;
  final String? message;
  final T? data;
  final List<String>? errors;

  const ApiResponse({
    this.success = true,
    this.message,
    this.data,
    this.errors,
  });

  factory ApiResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic json)? fromJsonT,
  ) {
    final status = json['status'];
    final isSuccess = json['success'] as bool? ?? (status == 'success' || status == 200);
    return ApiResponse<T>(
      success: isSuccess,
      message: json['message'] as String?,
      data: json['data'] != null && fromJsonT != null ? fromJsonT(json['data']) : json['data'] as T?,
      errors: json['errors'] != null ? List<String>.from(json['errors'] as List) : null,
    );
  }
}

class PaginatedResponse<T> {
  final List<T> items;
  final int total;
  final int page;
  final int pageSize;
  final bool hasMore;

  const PaginatedResponse({
    required this.items,
    this.total = 0,
    this.page = 1,
    this.pageSize = 20,
    this.hasMore = false,
  });

  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Map<String, dynamic>) fromJsonT,
  ) {
    final rawList = json['content'] ?? json['items'] ?? json['data'] ?? [];
    final List<T> list = (rawList as List)
        .map((e) => fromJsonT(Map<String, dynamic>.from(e as Map)))
        .toList();

    final totalElements = (json['totalElements'] ?? json['total'] ?? list.length) as int;
    final currentPage = (json['number'] ?? json['page'] ?? 1) as int;
    final size = (json['size'] ?? json['pageSize'] ?? 20) as int;

    return PaginatedResponse<T>(
      items: list,
      total: totalElements,
      page: currentPage,
      pageSize: size,
      hasMore: totalElements > (currentPage * size),
    );
  }
}
"""


def generar_base_crud_service() -> str:
    return """import '../network/api_client.dart';
import '../models/base_model.dart';

/// CRUD contra el backend. Los errores (red, 4xx, 5xx) se PROPAGAN como ApiException para que
/// la vista muestre el estado de error: antes se guardaba en memoria y se fingía éxito, y los
/// datos "creados" desaparecían al reiniciar la app.
abstract class BaseCrudService<T extends BaseModel> {
  final ApiClient client;
  final String endpoint;
  final T Function(Map<String, dynamic> json) fromJson;

  BaseCrudService({
    required this.endpoint,
    required this.fromJson,
    ApiClient? client,
  }) : client = client ?? ApiClient();

  List<dynamic> _comoLista(dynamic response) {
    if (response is List) return response;
    if (response is Map) {
      final contenido = response['content'] ?? response['items'] ?? response['data'];
      if (contenido is List) return contenido;
    }
    return const [];
  }

  T _comoModelo(dynamic response) => fromJson(Map<String, dynamic>.from(response as Map));

  Future<List<T>> getAll() async {
    final response = await client.get(endpoint);
    return _comoLista(response).map((item) => _comoModelo(item)).toList();
  }

  Future<T> getById(dynamic id) async => _comoModelo(await client.get('$endpoint/$id'));

  Future<T> create(Map<String, dynamic> data) async {
    final cuerpo = Map<String, dynamic>.from(data)..removeWhere((k, v) => k == 'id' && (v == null || v == ''));
    return _comoModelo(await client.post(endpoint, cuerpo));
  }

  Future<T> update(dynamic id, Map<String, dynamic> data) async =>
      _comoModelo(await client.put('$endpoint/$id', data));

  Future<void> delete(dynamic id) async {
    await client.delete('$endpoint/$id');
  }

  /// Método de negocio del diagrama: el backend lo expone como POST <endpoint>/<nombre>?param=valor
  Future<dynamic> accion(String nombre, [Map<String, dynamic> parametros = const {}]) {
    final query = parametros.entries
        .where((e) => e.value != null && e.value.toString().isNotEmpty)
        .map((e) => '${Uri.encodeQueryComponent(e.key)}=${Uri.encodeQueryComponent(e.value.toString())}')
        .join('&');
    return client.post('$endpoint/$nombre${query.isEmpty ? '' : '?$query'}', const <String, dynamic>{});
  }
}
"""


def construir_archivos_esqueleto(app_name: str, api_base_url: str) -> Dict[str, str]:
    return {
        "pubspec.yaml": generar_pubspec_yaml(app_name),
        "analysis_options.yaml": generar_analysis_options(),
        ".gitignore": generar_flutter_gitignore(),
        "README.md": generar_readme_flutter(app_name, api_base_url),
        ".env": generar_env(api_base_url),
        ".env.example": generar_env_example(),
        "lib/core/config/api_config.dart": generar_api_config(api_base_url),
        "lib/core/network/api_client.dart": generar_api_client(),
        "lib/core/models/base_model.dart": generar_base_model(),
        "lib/core/dto/base_dto.dart": generar_base_dto(),
        "lib/core/services/base_crud_service.dart": generar_base_crud_service(),
    }


