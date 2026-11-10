import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:movil/core/network/api_provider.dart';

/// Para mostrar avisos desde fuera de una pantalla (notificaciones con la app abierta).
final GlobalKey<ScaffoldMessengerState> mensajeroGlobal = GlobalKey<ScaffoldMessengerState>();

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

      // Con la app abierta Android/iOS NO muestran la notificación: se muestra un aviso en la app
      // (antes solo se imprimía en consola y las menciones "no llegaban").
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        final titulo = message.notification?.title ?? 'Notificación';
        final cuerpo = message.notification?.body ?? '';
        final esMencion = message.data['tipo'] == 'mencion';
        mensajeroGlobal.currentState
          ?..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 6),
            content: Row(
              children: [
                Icon(esMencion ? Icons.alternate_email : Icons.notifications_active_outlined,
                    color: esMencion ? const Color(0xFFFCC419) : Colors.white),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(titulo, style: const TextStyle(fontWeight: FontWeight.bold)),
                      if (cuerpo.isNotEmpty) Text(cuerpo, maxLines: 2, overflow: TextOverflow.ellipsis),
                    ],
                  ),
                ),
              ],
            ),
          ));
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

