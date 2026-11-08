import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../storage/local_storage_service.dart';
import 'interceptors/auth_interceptor.dart';

class ApiProvider {
  static final ApiProvider _instance = ApiProvider._internal();
  late Dio _dio;

  factory ApiProvider() {
    return _instance;
  }

  ApiProvider._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: LocalStorageService.baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(AuthInterceptor());

    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        request: true,
        requestHeader: true,
        requestBody: true,
        responseHeader: false,
        responseBody: true,
        error: true,
      ));
    }
  }

  void actualizarBaseUrl(String nuevaUrl) {
    LocalStorageService.setBaseUrl(nuevaUrl);
    _dio.options.baseUrl = LocalStorageService.baseUrl;
  }

  Dio get dioClient => _dio;

  Future<dynamic> get(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      _dio.options.baseUrl = LocalStorageService.baseUrl;
      final response = await _dio.get(
        path,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return _handleResponse(response);
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<dynamic> post(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      _dio.options.baseUrl = LocalStorageService.baseUrl;
      final response = await _dio.post(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return _handleResponse(response);
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<dynamic> put(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      _dio.options.baseUrl = LocalStorageService.baseUrl;
      final response = await _dio.put(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return _handleResponse(response);
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<dynamic> patch(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      _dio.options.baseUrl = LocalStorageService.baseUrl;
      final response = await _dio.patch(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return _handleResponse(response);
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<dynamic> delete(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      _dio.options.baseUrl = LocalStorageService.baseUrl;
      final response = await _dio.delete(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
        cancelToken: cancelToken,
      );
      return _handleResponse(response);
    } catch (e) {
      throw _handleError(e);
    }
  }

  dynamic _handleResponse(Response response) {
    if (response.statusCode != null &&
        response.statusCode! >= 200 &&
        response.statusCode! < 300) {
      return response.data;
    } else {
      throw Exception('Error del servidor: Código ${response.statusCode}');
    }
  }

  Exception _handleError(dynamic error) {
    if (error is DioException) {
      switch (error.type) {
        case DioExceptionType.connectionTimeout:
        case DioExceptionType.sendTimeout:
        case DioExceptionType.receiveTimeout:
          return Exception('Tiempo de espera agotado. Verifica tu conexión.');
        case DioExceptionType.badResponse:
          final statusCode = error.response?.statusCode;
          final detail = error.response?.data is Map
              ? (error.response?.data['detail'] ?? error.response?.data['message'])
              : null;
          return Exception(detail ?? 'Error $statusCode en la respuesta del servidor');
        case DioExceptionType.cancel:
          return Exception('La petición fue cancelada.');
        case DioExceptionType.connectionError:
          return Exception('No se pudo conectar al servidor en ${LocalStorageService.baseUrl}. Revisa la IP.');
        default:
          return Exception('Error de red: ${error.message}');
      }
    }
    return Exception('Ocurrió un error inesperado.');
  }
}

final api = ApiProvider();
