class ApiConfig {
  static const String baseUrl = 'http://localhost:8080';
  static const Duration timeout = Duration(seconds: 20);

  static Map<String, String> defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
}

