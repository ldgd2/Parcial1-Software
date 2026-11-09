import 'package:flutter/foundation.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:movil/core/network/api_provider.dart';

class PushNotificationService {
  static bool _inicializado = false;
  static String? _tokenActual;

  static String? get tokenActual => _tokenActual;

  static Future<void> inicializar() async {
    if (_inicializado) return;

    try {
      await Firebase.initializeApp();

      final messaging = FirebaseMessaging.instance;

      final settings = await messaging.requestPermission(
        alert: true,
        announcement: false,
        badge: true,
        carPlay: false,
        criticalAlert: false,
        provisional: false,
        sound: true,
      );

      if (kDebugMode) {
        print('[PushNotificationService] Permisos FCM: ${settings.authorizationStatus}');
      }

      _tokenActual = await messaging.getToken();
      if (kDebugMode && _tokenActual != null) {
        print('[PushNotificationService] FCM Token obtenido: ${_tokenActual!.substring(0, 20)}...');
      }

      messaging.onTokenRefresh.listen((nuevoToken) {
        _tokenActual = nuevoToken;
        registrarTokenDispositivo();
      });

      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        if (kDebugMode) {
          print('[PushNotificationService] Notificacion en primer plano: ${message.notification?.title}');
        }
      });

      _inicializado = true;
    } catch (e) {
      if (kDebugMode) {
        print('[PushNotificationService] Error al inicializar Firebase: $e');
      }
    }
  }

  static Future<void> registrarTokenDispositivo({int? userId}) async {
    try {
      if (_tokenActual == null) {
        final messaging = FirebaseMessaging.instance;
        _tokenActual = await messaging.getToken();
      }

      final token = _tokenActual;
      if (token == null || token.isEmpty) return;

      // 1. Guardar en dispositivos_push
      try {
        await api.post(
          '/api/notificaciones/dispositivos',
          data: {
            'token': token,
            'plataforma': defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android',
          },
        );
      } catch (e) {
        if (kDebugMode) {
          print('[PushNotificationService] Error al registrar en dispositivos_push: $e');
        }
      }

      // 2. Guardar en tabla notifications si hay userId
      if (userId != null && userId > 0) {
        try {
          await api.post(
            '/api/notifications/register',
            data: {
              'user_id': userId,
              'device_token': token,
            },
          );
        } catch (_) {}
      }
    } catch (e) {
      if (kDebugMode) {
        print('[PushNotificationService] Error registrando token FCM: $e');
      }
    }
  }
}

