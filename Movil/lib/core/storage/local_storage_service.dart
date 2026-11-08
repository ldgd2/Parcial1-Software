import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class LocalStorageService {
  static String? _token;
  static Map<String, dynamic>? _usuario;
  static String? _baseUrlPersonalizada;

  static final List<String> _codigosRecientes = [];

  static String sanitizarUrl(String url) {
    var limpia = url.trim();
    if (limpia.isEmpty) return limpia;

    if (!limpia.startsWith('http://') && !limpia.startsWith('https://')) {
      if (limpia.startsWith('localhost') ||
          limpia.startsWith('127.0.0.1') ||
          limpia.startsWith('10.0.2.2') ||
          limpia.startsWith('192.168.') ||
          limpia.startsWith('10.') ||
          limpia.contains(':8000') ||
          limpia.contains(':3000')) {
        limpia = 'http://$limpia';
      } else {
        limpia = 'https://$limpia';
      }
    }

    while (limpia.endsWith('/')) {
      limpia = limpia.substring(0, limpia.length - 1);
    }

    return limpia;
  }

  static String get baseUrl {
    if (_baseUrlPersonalizada != null && _baseUrlPersonalizada!.isNotEmpty) {
      return sanitizarUrl(_baseUrlPersonalizada!);
    }
    String? envUrl;
    if (dotenv.isInitialized) {
      envUrl = dotenv.env['API_BASE_URL'];
    }
    if (envUrl != null && envUrl.trim().isNotEmpty) {
      return sanitizarUrl(envUrl);
    }
    return kIsWeb
        ? 'http://127.0.0.1:8000'
        : (defaultTargetPlatform == TargetPlatform.android
            ? 'http://10.0.2.2:8000'
            : 'http://127.0.0.1:8000');
  }

  static String? get token => _token;
  static Map<String, dynamic>? get usuario => _usuario;
  static List<String> get codigosRecientes => List.unmodifiable(_codigosRecientes);

  static bool get isAuthenticated => _token != null && _token!.isNotEmpty;

  static void guardarSesion({
    required String token,
    Map<String, dynamic>? usuario,
  }) {
    _token = token;
    _usuario = usuario;
  }

  static void setBaseUrl(String url) {
    if (url.trim().isNotEmpty) {
      _baseUrlPersonalizada = sanitizarUrl(url);
    }
  }

  static void agregarCodigoReciente(String codigo) {
    final limpio = codigo.trim().toUpperCase();
    if (limpio.isNotEmpty) {
      _codigosRecientes.remove(limpio);
      _codigosRecientes.insert(0, limpio);
      if (_codigosRecientes.length > 5) {
        _codigosRecientes.removeLast();
      }
    }
  }

  static void cerrarSesion() {
    _token = null;
    _usuario = null;
  }
}
