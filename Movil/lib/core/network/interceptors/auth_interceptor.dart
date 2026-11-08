import 'package:dio/dio.dart';
import 'package:movil/core/storage/local_storage_service.dart';

class AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = LocalStorageService.token;
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    super.onRequest(options, handler);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.response?.statusCode == 401) {
      LocalStorageService.cerrarSesion();
    }
    super.onError(err, handler);
  }
}
