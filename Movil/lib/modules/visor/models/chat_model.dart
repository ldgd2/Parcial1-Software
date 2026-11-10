import 'dart:ui';

/// Mensaje del chat de la sala (mismo formato que la web: ChatMessage de chatTypes.ts).
class ChatMensajeModel {
  final String id;
  final String senderId;
  final String senderName;
  final String senderColor;
  final String text;
  final int timestamp;
  final bool isAi;
  final String? summary;
  final String? aiStatus;
  final String? mediaTipo; // 'imagen' | 'audio' (solo se muestra un aviso en el móvil)
  final String? replyToName;
  final String? replyToText;

  const ChatMensajeModel({
    required this.id,
    required this.senderId,
    required this.senderName,
    required this.senderColor,
    required this.text,
    required this.timestamp,
    this.isAi = false,
    this.summary,
    this.aiStatus,
    this.mediaTipo,
    this.replyToName,
    this.replyToText,
  });

  factory ChatMensajeModel.fromJson(Map<String, dynamic> j) {
    final media = j['media'];
    final reply = j['replyTo'];
    return ChatMensajeModel(
      id: (j['id'] ?? '').toString(),
      senderId: (j['senderId'] ?? '').toString(),
      senderName: (j['senderName'] ?? 'Alguien').toString(),
      senderColor: (j['senderColor'] ?? '#25D366').toString(),
      text: (j['text'] ?? '').toString(),
      timestamp: (j['timestamp'] is num) ? (j['timestamp'] as num).toInt() : DateTime.now().millisecondsSinceEpoch,
      isAi: j['isAi'] == true,
      summary: j['summary']?.toString(),
      aiStatus: j['aiStatus']?.toString(),
      mediaTipo: media is Map ? (media['tipo'] ?? media['type'] ?? 'archivo').toString() : null,
      replyToName: reply is Map ? reply['senderName']?.toString() : null,
      replyToText: reply is Map ? reply['text']?.toString() : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'senderId': senderId,
        'senderName': senderName,
        'senderColor': senderColor,
        'text': text,
        'timestamp': timestamp,
      };

  /// Texto a mostrar: las respuestas de la IA traen el resumen aparte.
  String get textoVisible {
    if (isAi && (summary ?? '').isNotEmpty && text.trim().isEmpty) return summary!;
    return text;
  }

  Color get color {
    final hex = senderColor.replaceAll('#', '');
    final v = int.tryParse(hex.length == 6 ? 'FF$hex' : hex, radix: 16);
    return v != null ? Color(v) : const Color(0xFF25D366);
  }
}

/// Alguien conectado a la sala ahora mismo (mensaje `presence` del servidor).
class UsuarioEnLinea {
  final String id;
  final String nickname;
  final String role;
  final String device;

  const UsuarioEnLinea({required this.id, required this.nickname, required this.role, required this.device});

  factory UsuarioEnLinea.fromJson(Map<String, dynamic> j) => UsuarioEnLinea(
        id: (j['id'] ?? '').toString(),
        nickname: (j['nickname'] ?? 'Invitado').toString(),
        role: (j['role'] ?? 'view').toString(),
        device: (j['device'] ?? 'web').toString(),
      );

  bool get esMovil => device == 'movil';
  bool get esAnfitrion => role == 'host';
}

/// Color estable por persona.
String colorDeUsuario(String clave) {
  const paleta = ['#25D366', '#34B7F1', '#FF6B6B', '#FFA94D', '#845EF7', '#20C997', '#F06595', '#FCC419'];
  var h = 0;
  for (final c in clave.codeUnits) {
    h = (h * 31 + c) & 0x7fffffff;
  }
  return paleta[h % paleta.length];
}

String normalizar(String s) {
  const con = 'áàäâéèëêíìïîóòöôúùüûñÁÀÄÂÉÈËÊÍÌÏÎÓÒÖÔÚÙÜÛÑ';
  const sin = 'aaaaeeeeiiiioooouuuunAAAAEEEEIIIIOOOOUUUUN';
  final b = StringBuffer();
  for (final ch in s.split('')) {
    final i = con.indexOf(ch);
    b.write(i >= 0 ? sin[i] : ch);
  }
  return b.toString().toLowerCase().trim();
}

/// ¿El texto me menciona? (`@Ana`, `@Ana Pérez`, `@todos`)
bool meMenciona(String texto, String miNombre) {
  final t = normalizar(texto);
  if (!t.contains('@')) return false;
  final nombre = normalizar(miNombre);
  if (nombre.isEmpty) return false;
  final etiquetas = RegExp(r'@([a-z0-9_.\-]+)').allMatches(t).map((m) => m.group(1)!).toSet();
  if (etiquetas.intersection({'todos', 'all', 'everyone', 'sala'}).isNotEmpty) return true;
  final partes = nombre.split(RegExp(r'\s+'));
  return t.contains('@$nombre') || etiquetas.contains(partes.first) || etiquetas.contains(partes.join());
}
