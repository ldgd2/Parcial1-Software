import 'package:movil/core/network/api_provider.dart';
import 'package:movil/modules/auth/models/user_model.dart';
import 'package:movil/modules/auth/services/auth_endpoints.dart';

class AuthService {
  final ApiProvider _api;

  AuthService({ApiProvider? apiProvider}) : _api = apiProvider ?? api;

  Future<AuthTokenResponse> login(String email, String password) async {
    final response = await _api.post(
      AuthEndpoints.login,
      data: {
        'email': email.trim(),
        'password': password,
      },
    );
    return AuthTokenResponse.fromJson(response as Map<String, dynamic>);
  }

  Future<AuthTokenResponse> ingresoAnonimo(String nombre) async {
    final response = await _api.post(
      AuthEndpoints.ingresoAnonimo,
      data: {
        'nombre': nombre.trim(),
      },
    );
    return AuthTokenResponse.fromJson(response as Map<String, dynamic>);
  }
}

