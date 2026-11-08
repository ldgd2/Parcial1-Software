import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:movil/core/storage/local_storage_service.dart';

typedef OnDiagramEvent = void Function(Map<String, dynamic> event);
typedef OnCanvasRefresh = void Function();

class VisorWebSocket {
  final String codigoAcceso;
  final String guestId;
  final String nickname;
  final OnDiagramEvent? onDiagramEvent;
  final OnCanvasRefresh? onCanvasRefresh;

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

      _socket!.listen(
        _manejarMensaje,
        onError: (err) {
          _estaConectado = false;
          _programarReconexion();
        },
        onDone: () {
          _estaConectado = false;
          _programarReconexion();
        },
      );

      // Solicitar snapshots iniciales
      _enviar({
        'type': 'request_snapshots',
      });

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

