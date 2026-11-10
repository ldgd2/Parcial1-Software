import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:movil/core/storage/local_storage_service.dart';

typedef OnDiagramEvent = void Function(Map<String, dynamic> event);
typedef OnCanvasRefresh = void Function();
typedef OnChatMensaje = void Function(Map<String, dynamic> mensaje);
typedef OnChatHistorial = void Function(List<Map<String, dynamic>> mensajes);
typedef OnPresencia = void Function(List<Map<String, dynamic>> usuarios);
typedef OnEstadoConexion = void Function(bool conectado);

class VisorWebSocket {
  final String codigoAcceso;
  final String guestId;
  final String nickname;
  final OnDiagramEvent? onDiagramEvent;
  final OnCanvasRefresh? onCanvasRefresh;
  final OnChatMensaje? onChatMensaje;
  final OnChatHistorial? onChatHistorial;
  final OnPresencia? onPresencia;
  final OnEstadoConexion? onEstadoConexion;

  WebSocket? _socket;
  bool _estaConectado = false;
  bool _desconexionIntencional = false;
  Timer? _reconnectTimer;
  Timer? _pingTimer;

  bool get estaConectado => _estaConectado;

  VisorWebSocket({
    required this.codigoAcceso,
    required this.guestId,
    required this.nickname,
    this.onDiagramEvent,
    this.onCanvasRefresh,
    this.onChatMensaje,
    this.onChatHistorial,
    this.onPresencia,
    this.onEstadoConexion,
  });

  String _construirUrlWs() {
    final base = LocalStorageService.baseUrl;
    String wsBase;
    if (base.startsWith('https://')) {
      wsBase = 'wss://${base.substring(8)}';
    } else if (base.startsWith('http://')) {
      wsBase = 'ws://${base.substring(7)}';
    } else {
      wsBase = 'ws://$base';
    }

    final nickEncoded = Uri.encodeComponent(nickname.isNotEmpty ? nickname : 'Viewer');
    final gId = guestId.isNotEmpty ? guestId : 'mob_${DateTime.now().millisecondsSinceEpoch}';
    return '$wsBase/ws/salas/$codigoAcceso?user_type=viewer&guest_id=$gId&nickname=$nickEncoded';
  }

  Future<void> conectar() async {
    _desconexionIntencional = false;
    _reconnectTimer?.cancel();

    final url = _construirUrlWs();
    try {
      _socket = await WebSocket.connect(url).timeout(const Duration(seconds: 10));
      _estaConectado = true;

      // Un usuario con cuenta (guest_id auth_<id>) prueba su identidad con el token en el PRIMER mensaje
      if (guestId.startsWith('auth_') && (LocalStorageService.token ?? '').isNotEmpty) {
        _socket!.add(json.encode({'type': 'auth', 'token': LocalStorageService.token}));
      }
      onEstadoConexion?.call(true);

      _socket!.listen(
        _manejarMensaje,
        onError: (err) {
          _estaConectado = false;
          onEstadoConexion?.call(false);
          _programarReconexion();
        },
        onDone: () {
          _estaConectado = false;
          onEstadoConexion?.call(false);
          _programarReconexion();
        },
      );

      // Solicitar snapshots iniciales
      _enviar({'type': 'request_snapshots'});
      _enviar({'type': 'request_chat_history'});
      _enviar({'type': 'get_presence'});

      // Heartbeat periódico
      _pingTimer?.cancel();
      _pingTimer = Timer.periodic(const Duration(seconds: 25), (_) {
        if (_estaConectado && _socket != null) {
          _enviar({'type': 'ping'});
        }
      });
    } catch (e) {
      _estaConectado = false;
      _programarReconexion();
    }
  }

  void _manejarMensaje(dynamic data) {
    try {
      final decoded = json.decode(data.toString());
      if (decoded is! Map<String, dynamic>) return;

      final type = decoded['type'];
      switch (type) {
        case 'diagram_event':
          final payload = decoded['payload'];
          if (payload is Map<String, dynamic> && onDiagramEvent != null) {
            onDiagramEvent!(payload);
          } else {
            onCanvasRefresh?.call();
          }
          break;

        case 'diagram_delta':
        case 'snapshots_response':
        case 'tareas_actualizadas':
          onCanvasRefresh?.call();
          break;

        case 'admission_status':
          if (decoded['approved'] == true) {
            onCanvasRefresh?.call();
            _enviar({'type': 'request_chat_history'});
            _enviar({'type': 'get_presence'});
          }
          break;

        case 'chat_message':
          final m = decoded['message'];
          if (m is Map) onChatMensaje?.call(Map<String, dynamic>.from(m));
          break;

        case 'chat_history':
          final lista = decoded['messages'];
          if (lista is List) {
            onChatHistorial?.call(lista.whereType<Map>().map((m) => Map<String, dynamic>.from(m)).toList());
          }
          break;

        case 'presence':
          final usuarios = decoded['users'];
          if (usuarios is List) {
            onPresencia?.call(usuarios.whereType<Map>().map((u) => Map<String, dynamic>.from(u)).toList());
          }
          break;

        default:
          break;
      }
    } catch (e) {
      if (kDebugMode) {
        print('Error procesando WS message: $e');
      }
    }
  }

  /// Envía un mensaje al chat de la sala. Devuelve false si no hay conexión.
  bool enviarChat(Map<String, dynamic> mensaje) {
    if (!_estaConectado || _socket == null) return false;
    _enviar({'type': 'chat_message', 'message': mensaje});
    return true;
  }

  void _enviar(Map<String, dynamic> data) {
    if (_estaConectado && _socket != null) {
      try {
        _socket!.add(json.encode(data));
      } catch (_) {}
    }
  }

  void _programarReconexion() {
    if (_desconexionIntencional) return;
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 3), () {
      if (!_desconexionIntencional) {
        conectar();
      }
    });
  }

  void desconectar() {
    _desconexionIntencional = true;
    _estaConectado = false;
    _reconnectTimer?.cancel();
    _pingTimer?.cancel();
    _socket?.close();
    _socket = null;
  }
}

