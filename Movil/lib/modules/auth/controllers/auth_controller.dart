import 'package:flutter/material.dart';
import 'package:movil/core/storage/local_storage_service.dart';
import 'package:movil/core/services/push_notification_service.dart';
import 'package:movil/modules/auth/models/user_model.dart';
import 'package:movil/modules/auth/services/auth_service.dart';

class AuthController extends ChangeNotifier {
  final AuthService _authService;

  AuthController({AuthService? authService})
      : _authService = authService ?? AuthService();

  bool _isLoading = false;
  String? _errorMessage;
  UserModel? _currentUser;

  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  UserModel? get currentUser => _currentUser;
  bool get isAuthenticated => LocalStorageService.isAuthenticated;

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _authService.login(email, password);
      _currentUser = res.usuario;
      LocalStorageService.guardarSesion(
        token: res.accessToken,
        usuario: res.usuario?.toJson(),
      );
      // Registrar token FCM en el backend para recibir campanas y notificaciones
      PushNotificationService.registrarTokenDispositivo(userId: res.usuario?.id);
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _errorMessage = e.toString().replaceAll('Exception: ', '');
      notifyListeners();
      return false;
    }
  }

  Future<bool> ingresoAnonimo(String nombre) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _authService.ingresoAnonimo(nombre);
      _currentUser = res.usuario ?? UserModel(id: 0, nombre: nombre, email: '', esAnonimo: true);
      LocalStorageService.guardarSesion(
        token: res.accessToken,
        usuario: _currentUser?.toJson(),
      );
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _errorMessage = e.toString().replaceAll('Exception: ', '');
      notifyListeners();
      return false;
    }
  }

  void cerrarSesion() {
    LocalStorageService.cerrarSesion();
    _currentUser = null;
    notifyListeners();
  }
}

