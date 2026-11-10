import 'package:flutter/material.dart';
import 'package:movil/modules/visor/controllers/visor_controller.dart';
import 'package:movil/modules/visor/models/chat_model.dart';
import 'package:movil/shared/utils/ui_engine/tema.dart';

/// Chat de la sala (el mismo que el panel de la web): historial, mensajes en vivo,
/// quién está en línea y menciones con @.
class ChatSheet extends StatefulWidget {
  final VisorController controller;

  const ChatSheet({super.key, required this.controller});

  @override
  State<ChatSheet> createState() => _ChatSheetState();
}

class _ChatSheetState extends State<ChatSheet> {
  final _texto = TextEditingController();
  final _scroll = ScrollController();
  final _foco = FocusNode();
  int _ultimaCantidad = 0;
  String? _filtroMencion;

  VisorController get _c => widget.controller;

  @override
  void initState() {
    super.initState();
    _c.addListener(_alCambiar);
    _texto.addListener(_detectarMencion);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _c.marcarChatAbierto(true);
      _bajar(animado: false);
    });
  }

  @override
  void dispose() {
    _c.removeListener(_alCambiar);
    _c.marcarChatAbierto(false);
    _texto.dispose();
    _scroll.dispose();
    _foco.dispose();
    super.dispose();
  }

  void _alCambiar() {
    if (!mounted) return;
    setState(() {});
    if (_c.mensajes.length != _ultimaCantidad) {
      _ultimaCantidad = _c.mensajes.length;
      WidgetsBinding.instance.addPostFrameCallback((_) => _bajar());
    }
  }

  void _bajar({bool animado = true}) {
    if (!_scroll.hasClients) return;
    final fin = _scroll.position.maxScrollExtent;
    if (animado) {
      _scroll.animateTo(fin, duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
    } else {
      _scroll.jumpTo(fin);
    }
  }

  void _detectarMencion() {
    final t = _texto.text;
    final pos = _texto.selection.baseOffset < 0 ? t.length : _texto.selection.baseOffset;
    final antes = t.substring(0, pos.clamp(0, t.length));
    final m = RegExp(r'(?:^|\s)@([\wáéíóúñÁÉÍÓÚÑ.\-]*)$').firstMatch(antes);
    final nuevo = m?.group(1);
    if (nuevo != _filtroMencion) setState(() => _filtroMencion = nuevo);
  }

  List<String> get _sugerencias {
    final f = normalizar(_filtroMencion ?? '');
    final nombres = <String>{'diag', 'todos'};
    for (final u in _c.enLinea) {
      if (normalizar(u.nickname) != normalizar(_c.miNombre)) nombres.add(u.nickname);
    }
    for (final m in _c.mensajes) {
      if (!m.isAi && m.senderId != _c.miSenderId) nombres.add(m.senderName);
    }
    return nombres.where((n) => normalizar(n).contains(f)).take(8).toList();
  }

  void _elegirMencion(String nombre) {
    final t = _texto.text;
    final pos = _texto.selection.baseOffset < 0 ? t.length : _texto.selection.baseOffset;
    final antes = t.substring(0, pos).replaceFirst(RegExp(r'@[\wáéíóúñÁÉÍÓÚÑ.\-]*$'), '@$nombre ');
    final despues = t.substring(pos);
    _texto.value = TextEditingValue(
      text: antes + despues,
      selection: TextSelection.collapsed(offset: antes.length),
    );
    _foco.requestFocus();
  }

  void _enviar() {
    if (_c.enviarMensaje(_texto.text)) {
      _texto.clear();
    } else if (_texto.text.trim().isNotEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sin conexión con la sala. Reintentando…')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final colores = AppColores.oscuro;
    final textos = AppTextos.generar(colores);
    final mensajes = _c.mensajes;
    final alto = MediaQuery.of(context).size.height * 0.86;

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        height: alto,
        decoration: BoxDecoration(
          color: colores.fondo,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(18)),
          border: Border.all(color: colores.borde),
        ),
        child: Column(
          children: [
            _cabecera(colores, textos),
            Divider(height: 1, color: colores.borde),
            Expanded(
              child: mensajes.isEmpty
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.all(32),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.chat_bubble_outline, size: 40, color: colores.secundario),
                            const SizedBox(height: 10),
                            Text('Aún no hay mensajes', style: textos.subtitulo.copyWith(fontSize: 15)),
                            const SizedBox(height: 4),
                            Text('Escribe a tu equipo. Usa @nombre para mencionar a alguien.',
                                textAlign: TextAlign.center, style: textos.cuerpoPequeno),
                          ],
                        ),
                      ),
                    )
                  : ListView.builder(
                      controller: _scroll,
                      padding: const EdgeInsets.fromLTRB(10, 12, 10, 12),
                      itemCount: mensajes.length,
                      itemBuilder: (_, i) {
                        final m = mensajes[i];
                        final anterior = i > 0 ? mensajes[i - 1] : null;
                        final mostrarNombre = anterior == null || anterior.senderId != m.senderId;
                        return _Burbuja(
                          mensaje: m,
                          propio: m.senderId == _c.miSenderId,
                          mostrarNombre: mostrarNombre,
                          meMenciona: !m.isAi && m.senderId != _c.miSenderId && meMenciona(m.text, _c.miNombre),
                          colores: colores,
                        );
                      },
                    ),
            ),
            if (_filtroMencion != null && _sugerencias.isNotEmpty) _barraMenciones(colores),
            _entrada(colores),
          ],
        ),
      ),
    );
  }

  Widget _cabecera(AppColores colores, AppTextos textos) {
    final enLinea = _c.enLinea;
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 10, 8, 10),
      child: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(color: const Color(0xFF25D366).withValues(alpha: 0.15), shape: BoxShape.circle),
            child: const Icon(Icons.forum_outlined, color: Color(0xFF25D366), size: 20),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Chat de la sala', style: textos.titulo.copyWith(fontSize: 16)),
                const SizedBox(height: 2),
                GestureDetector(
                  onTap: enLinea.isEmpty ? null : () => _mostrarConectados(colores, textos),
                  child: Row(
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: _c.wsConectado ? const Color(0xFF25D366) : colores.textoSecundario,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          _c.wsConectado
                              ? '${_c.cantidadEnLinea} en línea · ${enLinea.map((u) => u.nickname).toSet().take(3).join(', ')}'
                              : 'Conectando…',
                          overflow: TextOverflow.ellipsis,
                          style: textos.cuerpoPequeno.copyWith(fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close),
            onPressed: () => Navigator.pop(context),
          ),
        ],
      ),
    );
  }

  void _mostrarConectados(AppColores colores, AppTextos textos) {
    showModalBottomSheet(
      context: context,
      backgroundColor: colores.fondoSecundario,
      builder: (_) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.symmetric(vertical: 12),
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
              child: Text('En línea ahora', style: textos.titulo.copyWith(fontSize: 15)),
            ),
            ..._c.enLinea.map((u) => ListTile(
                  leading: CircleAvatar(
                    backgroundColor: ChatMensajeModel(
                      id: '', senderId: '', senderName: '', text: '', timestamp: 0,
                      senderColor: colorDeUsuario(u.id),
                    ).color,
                    child: Text(u.nickname.isNotEmpty ? u.nickname[0].toUpperCase() : '?',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  ),
                  title: Text(u.nickname, style: textos.cuerpo),
                  subtitle: Text(
                    '${u.esAnfitrion ? 'Anfitrión' : (u.role == 'edit' ? 'Editor' : 'Lector')} · ${u.esMovil ? 'App móvil' : 'Web'}',
                    style: textos.cuerpoPequeno,
                  ),
                  trailing: Icon(u.esMovil ? Icons.phone_android : Icons.computer, size: 18, color: colores.secundario),
                )),
          ],
        ),
      ),
    );
  }

  Widget _barraMenciones(AppColores colores) {
    return Container(
      height: 46,
      color: colores.fondoSecundario,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
        children: _sugerencias
            .map((n) => Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: ActionChip(
                    avatar: Icon(n == 'diag' ? Icons.auto_awesome : Icons.alternate_email, size: 16),
                    label: Text(n),
                    onPressed: () => _elegirMencion(n),
                  ),
                ))
            .toList(),
      ),
    );
  }

  Widget _entrada(AppColores colores) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(10, 6, 10, 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: _texto,
                focusNode: _foco,
                minLines: 1,
                maxLines: 5,
                textCapitalization: TextCapitalization.sentences,
                onSubmitted: (_) => _enviar(),
                decoration: InputDecoration(
                  hintText: 'Mensaje… (@ para mencionar)',
                  filled: true,
                  fillColor: colores.fondoSecundario,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
                ),
              ),
            ),
            const SizedBox(width: 8),
            ValueListenableBuilder<TextEditingValue>(
              valueListenable: _texto,
              builder: (_, v, _) => AnimatedScale(
                scale: v.text.trim().isEmpty ? 0.85 : 1,
                duration: const Duration(milliseconds: 150),
                child: FloatingActionButton.small(
                  heroTag: 'enviar_chat',
                  backgroundColor: const Color(0xFF25D366),
                  foregroundColor: Colors.white,
                  onPressed: v.text.trim().isEmpty ? null : _enviar,
                  child: const Icon(Icons.send, size: 18),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Burbuja extends StatelessWidget {
  final ChatMensajeModel mensaje;
  final bool propio;
  final bool mostrarNombre;
  final bool meMenciona;
  final AppColores colores;

  const _Burbuja({
    required this.mensaje,
    required this.propio,
    required this.mostrarNombre,
    required this.meMenciona,
    required this.colores,
  });

  String _hora(int ms) {
    final d = DateTime.fromMillisecondsSinceEpoch(ms);
    return '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
  }

  List<TextSpan> _resaltar(String texto, Color base) {
    final spans = <TextSpan>[];
    final re = RegExp(r'([@/][\wáéíóúñÁÉÍÓÚÑ.\-]+)');
    var i = 0;
    for (final m in re.allMatches(texto)) {
      if (m.start > 0 && !RegExp(r'\s').hasMatch(texto[m.start - 1])) continue;
      if (m.start > i) spans.add(TextSpan(text: texto.substring(i, m.start)));
      spans.add(TextSpan(
        text: m.group(0),
        style: const TextStyle(color: Color(0xFF34B7F1), fontWeight: FontWeight.w600),
      ));
      i = m.end;
    }
    if (i < texto.length) spans.add(TextSpan(text: texto.substring(i)));
    return spans;
  }

  @override
  Widget build(BuildContext context) {
    final fondo = propio
        ? const Color(0xFF005C4B)
        : (meMenciona ? const Color(0xFF3A3000) : colores.fondoSecundario);
    final texto = mensaje.textoVisible;
    final pendienteIA = mensaje.isAi && mensaje.aiStatus == 'pending';

    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: const Duration(milliseconds: 220),
      curve: Curves.easeOut,
      builder: (_, v, child) => Opacity(
        opacity: v,
        child: Transform.translate(offset: Offset(0, (1 - v) * 8), child: child),
      ),
      child: Align(
        alignment: propio ? Alignment.centerRight : Alignment.centerLeft,
        child: Container(
          margin: EdgeInsets.only(top: mostrarNombre ? 8 : 2, left: propio ? 48 : 0, right: propio ? 0 : 48),
          padding: const EdgeInsets.fromLTRB(11, 7, 11, 6),
          decoration: BoxDecoration(
            color: fondo,
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(14),
              topRight: const Radius.circular(14),
              bottomLeft: Radius.circular(propio ? 14 : 4),
              bottomRight: Radius.circular(propio ? 4 : 14),
            ),
            border: meMenciona ? Border.all(color: const Color(0xFFFCC419), width: 1) : null,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!propio && mostrarNombre)
                Padding(
                  padding: const EdgeInsets.only(bottom: 2),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (mensaje.isAi) ...[
                        const Icon(Icons.auto_awesome, size: 13, color: Color(0xFF25D366)),
                        const SizedBox(width: 4),
                      ],
                      Text(mensaje.senderName,
                          style: TextStyle(color: mensaje.color, fontWeight: FontWeight.bold, fontSize: 12.5)),
                    ],
                  ),
                ),
              if (mensaje.replyToName != null)
                Container(
                  margin: const EdgeInsets.only(bottom: 4),
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.black.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: const Border(left: BorderSide(color: Color(0xFF34B7F1), width: 3)),
                  ),
                  child: Text(
                    '${mensaje.replyToName}: ${mensaje.replyToText ?? ''}',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(color: colores.textoSecundario, fontSize: 12),
                  ),
                ),
              if (mensaje.mediaTipo != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(mensaje.mediaTipo!.contains('audio') ? Icons.mic : Icons.image_outlined,
                          size: 16, color: colores.textoSecundario),
                      const SizedBox(width: 4),
                      Text(mensaje.mediaTipo!.contains('audio') ? 'Nota de voz (ver en la web)' : 'Foto (ver en la web)',
                          style: TextStyle(color: colores.textoSecundario, fontSize: 12, fontStyle: FontStyle.italic)),
                    ],
                  ),
                ),
              if (pendienteIA)
                Text('Pensando…', style: TextStyle(color: colores.textoSecundario, fontStyle: FontStyle.italic))
              else if (texto.isNotEmpty)
                Text.rich(
                  TextSpan(children: _resaltar(texto, colores.textoPrincipal)),
                  style: TextStyle(color: colores.textoPrincipal, fontSize: 14.5, height: 1.3),
                ),
              const SizedBox(height: 2),
              Align(
                alignment: Alignment.bottomRight,
                child: Text(_hora(mensaje.timestamp),
                    style: TextStyle(color: colores.textoSecundario.withValues(alpha: 0.8), fontSize: 10.5)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
