class UserModel {
  final int id;
  final String nombre;
  final String email;
  final bool esAnonimo;
  final String? avatarUrl;

  const UserModel({
    required this.id,
    required this.nombre,
    required this.email,
    required this.esAnonimo,
    this.avatarUrl,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['usuario_id'] ?? json['id'] ?? 0,
      nombre: json['nombre'] ?? 'Usuario',
      email: json['email'] ?? '',
      esAnonimo: json['es_anonimo'] ?? false,
      avatarUrl: json['avatar_url'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nombre': nombre,
      'email': email,
      'es_anonimo': esAnonimo,
      'avatar_url': avatarUrl,
    };
  }
}

class AuthTokenResponse {
  final String accessToken;
  final String tokenType;
  final UserModel? usuario;

  const AuthTokenResponse({
    required this.accessToken,
    required this.tokenType,
    this.usuario,
  });

  factory AuthTokenResponse.fromJson(Map<String, dynamic> json) {
    UserModel? user;
    if (json.containsKey('usuario_id') || json.containsKey('nombre')) {
      user = UserModel.fromJson(json);
    }
    return AuthTokenResponse(
      accessToken: json['access_token'] ?? '',
      tokenType: json['token_type'] ?? 'bearer',
      usuario: user,
    );
  }
}

