from typing import Dict


def generar_pubspec_yaml(app_name: str) -> str:
    safe_name = app_name.lower().replace("-", "_").replace(" ", "_")
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

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
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

## Configuración y Ejecución
1. Instalar dependencias:
   ```bash
   flutter pub get
   ```
2. Ejecutar en emulador o dispositivo físico:
   ```bash
   flutter run
   ```
3. Si pruebas en emulador Android local, recuerda que `localhost` se accede como `http://10.0.2.2:8080`. Puedes modificar esta URL en `lib/core/config/api_config.dart`.
"""


def generar_api_config(api_base_url: str) -> str:
    clean_url = api_base_url.rstrip("/")
    return f"""class ApiConfig {{
  // URL base hacia los microservicios y endpoints REST del backend
  static const String baseUrl = '{clean_url}';
  static const Duration timeout = Duration(seconds: 20);

  static Map<String, String> defaultHeaders = {{
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }};
}}
"""


def generar_api_client() -> str:
    return """import 'dart:convert';
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
"""


def generar_app_theme() -> str:
    return """import 'package:flutter/material.dart';

class AppTheme {
  static const Color primaryColor = Color(0xFF2563EB);
  static const Color secondaryColor = Color(0xFF0F172A);
  static const Color accentColor = Color(0xFF38BDF8);
  static const Color backgroundColor = Color(0xFF0F172A);
  static const Color surfaceColor = Color(0xFF1E293B);
  static const Color cardColor = Color(0xFF1E293B);
  static const Color textColor = Color(0xFFF8FAFC);
  static const Color textMutedColor = Color(0xFF94A3B8);
  static const Color borderColor = Color(0xFF334155);

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      primaryColor: primaryColor,
      scaffoldBackgroundColor: backgroundColor,
      cardColor: cardColor,
      colorScheme: const ColorScheme.dark(
        primary: primaryColor,
        secondary: accentColor,
        surface: surfaceColor,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: surfaceColor,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: textColor,
          fontSize: 18,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.5,
        ),
        iconTheme: IconThemeData(color: textColor),
      ),
      cardTheme: CardTheme(
        color: surfaceColor,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: borderColor, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryColor,
          foregroundColor: Colors.white,
          elevation: 2,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceColor,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: borderColor),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: borderColor),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: primaryColor, width: 1.5),
        ),
        labelStyle: const TextStyle(color: textMutedColor),
        hintStyle: const TextStyle(color: textMutedColor),
      ),
    );
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
"""


def generar_app_text_field() -> str:
    return """import 'package:flutter/material.dart';

class AppTextField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final String? hint;
  final TextInputType keyboardType;
  final bool obscureText;
  final String? Function(String?)? validator;
  final IconData? prefixIcon;
  final int maxLines;

  const AppTextField({
    super.key,
    required this.controller,
    required this.label,
    this.hint,
    this.keyboardType = TextInputType.text,
    this.obscureText = false,
    this.validator,
    this.prefixIcon,
    this.maxLines = 1,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        obscureText: obscureText,
        maxLines: maxLines,
        validator: validator,
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          prefixIcon: prefixIcon != null ? Icon(prefixIcon, size: 20) : null,
        ),
      ),
    );
  }
}
"""


def generar_app_button() -> str:
    return """import 'package:flutter/material.dart';

class AppButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final IconData? icon;
  final Color? backgroundColor;

  const AppButton({
    super.key,
    required this.text,
    required this.onPressed,
    this.isLoading = false,
    this.icon,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: ElevatedButton(
        style: backgroundColor != null
            ? ElevatedButton.styleFrom(backgroundColor: backgroundColor)
            : null,
        onPressed: isLoading ? null : onPressed,
        child: isLoading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (icon != null) ...[
                    Icon(icon, size: 18),
                    const SizedBox(width: 8),
                  ],
                  Text(text),
                ],
              ),
      ),
    );
  }
}
"""


def generar_confirm_dialog() -> str:
    return """import 'package:flutter/material.dart';

class ConfirmDialog {
  static Future<bool> show({
    required BuildContext context,
    required String title,
    required String message,
    String confirmLabel = 'Eliminar',
    String cancelLabel = 'Cancelar',
    bool isDestructive = true,
  }) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: Color(0xFF334155)),
        ),
        title: Text(
          title,
          style: const TextStyle(color: Color(0xFFF8FAFC), fontSize: 18, fontWeight: FontWeight.bold),
        ),
        content: Text(
          message,
          style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 14),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(cancelLabel, style: const TextStyle(color: Color(0xFF94A3B8))),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: isDestructive ? const Color(0xFFEF4444) : const Color(0xFF2563EB),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(confirmLabel),
          ),
        ],
      ),
    );
    return result ?? false;
  }
}
"""


def generar_entity_card() -> str:
    return """import 'package:flutter/material.dart';

class EntityCard extends StatelessWidget {
  final String title;
  final String? subtitle;
  final String? trailingText;
  final IconData leadingIcon;
  final VoidCallback onTap;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  const EntityCard({
    super.key,
    required this.title,
    this.subtitle,
    this.trailingText,
    this.leadingIcon = Icons.layers_outlined,
    required this.onTap,
    this.onEdit,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: CircleAvatar(
          backgroundColor: const Color(0xFF2563EB).withValues(alpha: 0.15),
          child: Icon(leadingIcon, color: const Color(0xFF38BDF8), size: 20),
        ),
        title: Text(
          title,
          style: const TextStyle(color: Color(0xFFF8FAFC), fontWeight: FontWeight.w600, fontSize: 15),
        ),
        subtitle: subtitle != null
            ? Text(
                subtitle!,
                style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              )
            : null,
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (trailingText != null)
              Padding(
                padding: const EdgeInsets.only(right: 8.0),
                child: Text(
                  trailingText!,
                  style: const TextStyle(color: Color(0xFF38BDF8), fontWeight: FontWeight.bold),
                ),
              ),
            if (onEdit != null)
              IconButton(
                icon: const Icon(Icons.edit_outlined, size: 18, color: Color(0xFF94A3B8)),
                onPressed: onEdit,
                tooltip: 'Editar',
              ),
            if (onDelete != null)
              IconButton(
                icon: const Icon(Icons.delete_outline, size: 18, color: Color(0xFFEF4444)),
                onPressed: onDelete,
                tooltip: 'Eliminar',
              ),
          ],
        ),
        onTap: onTap,
      ),
    );
  }
}
"""


def generar_loading_widget() -> str:
    return """import 'package:flutter/material.dart';

class LoadingWidget extends StatelessWidget {
  final String? message;

  const LoadingWidget({super.key, this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(strokeWidth: 2.5),
          if (message != null) ...[
            const SizedBox(height: 12),
            Text(
              message!,
              style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
            ),
          ],
        ],
      ),
    );
  }
}
"""


def generar_empty_state_widget() -> str:
    return """import 'package:flutter/material.dart';

class EmptyStateWidget extends StatelessWidget {
  final String title;
  final String subtitle;
  final VoidCallback? onAction;
  final String? actionLabel;

  const EmptyStateWidget({
    super.key,
    this.title = 'Sin registros',
    this.subtitle = 'No se encontraron elementos disponibles.',
    this.onAction,
    this.actionLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.inbox_outlined, size: 48, color: Color(0xFF64748B)),
            const SizedBox(height: 12),
            Text(
              title,
              style: const TextStyle(
                color: Color(0xFFF8FAFC),
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
            ),
            if (onAction != null && actionLabel != null) ...[
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: onAction,
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
"""


def generar_error_state_widget() -> str:
    return """import 'package:flutter/material.dart';

class ErrorStateWidget extends StatelessWidget {
  final String error;
  final VoidCallback? onRetry;

  const ErrorStateWidget({super.key, required this.error, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Color(0xFFEF4444)),
            const SizedBox(height: 12),
            const Text(
              'Ocurrió un error',
              style: TextStyle(
                color: Color(0xFFF8FAFC),
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              error,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('Reintentar'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
"""


def construir_archivos_esqueleto(app_name: str, api_base_url: str) -> Dict[str, str]:
    return {
        "pubspec.yaml": generar_pubspec_yaml(app_name),
        "analysis_options.yaml": generar_analysis_options(),
        ".gitignore": generar_flutter_gitignore(),
        "README.md": generar_readme_flutter(app_name, api_base_url),
        "lib/core/config/api_config.dart": generar_api_config(api_base_url),
        "lib/core/network/api_client.dart": generar_api_client(),
        "lib/core/theme/app_theme.dart": generar_app_theme(),
        "lib/core/models/base_model.dart": generar_base_model(),
        "lib/core/dto/base_dto.dart": generar_base_dto(),
        "lib/core/services/base_crud_service.dart": generar_base_crud_service(),
        "lib/shared/widgets/app_text_field.dart": generar_app_text_field(),
        "lib/shared/widgets/app_button.dart": generar_app_button(),
        "lib/shared/widgets/confirm_dialog.dart": generar_confirm_dialog(),
        "lib/shared/widgets/entity_card.dart": generar_entity_card(),
        "lib/shared/widgets/loading_widget.dart": generar_loading_widget(),
        "lib/shared/widgets/empty_state_widget.dart": generar_empty_state_widget(),
        "lib/shared/widgets/error_state_widget.dart": generar_error_state_widget(),
    }


