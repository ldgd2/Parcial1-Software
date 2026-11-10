import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../app/modulo.dart';
import '../../core/network/api_client.dart';
import '../../core/utils/fmt.dart';
import 'entity_widgets.dart';

/// Abre la hoja para ejecutar una acción (método de negocio) y ver su resultado.
Future<void> mostrarAccion(BuildContext context, AccionInfo accion, Color color) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    builder: (context) => _AccionSheet(accion: accion, color: color),
  );
}

class _AccionSheet extends StatefulWidget {
  final AccionInfo accion;
  final Color color;
  const _AccionSheet({required this.accion, required this.color});

  @override
  State<_AccionSheet> createState() => _AccionSheetState();
}

class _AccionSheetState extends State<_AccionSheet> {
  final _formKey = GlobalKey<FormState>();
  late final Map<String, TextEditingController> _textos = {
    for (final p in widget.accion.parametros)
      if (p.tipo != 'booleano' && !p.tipo.startsWith('fecha')) p.nombre: TextEditingController(),
  };
  final Map<String, bool> _booleanos = {};
  final Map<String, DateTime?> _fechas = {};
  bool _ejecutando = false;
  String? _resultado;
  String? _error;

  @override
  void dispose() {
    for (final c in _textos.values) {
      c.dispose();
    }
    super.dispose();
  }

  Map<String, dynamic> _parametros() {
    final datos = <String, dynamic>{};
    for (final p in widget.accion.parametros) {
      final texto = _textos[p.nombre]?.text.trim() ?? '';
      switch (p.tipo) {
        case 'entero':
          datos[p.nombre] = int.tryParse(texto);
          break;
        case 'decimal':
          datos[p.nombre] = double.tryParse(texto.replaceAll(',', '.'));
          break;
        case 'booleano':
          datos[p.nombre] = _booleanos[p.nombre] ?? false;
          break;
        case 'fecha':
          datos[p.nombre] = _fechas[p.nombre]?.toIso8601String().substring(0, 10);
          break;
        case 'fechahora':
          datos[p.nombre] = _fechas[p.nombre]?.toIso8601String().substring(0, 19);
          break;
        default:
          datos[p.nombre] = texto;
      }
    }
    return datos;
  }

  Future<void> _ejecutar() async {
    if (!(_formKey.currentState?.validate() ?? true)) return;
    setState(() {
      _ejecutando = true;
      _resultado = null;
      _error = null;
    });
    try {
      final r = await widget.accion.ejecutar(_parametros());
      if (!mounted) return;
      HapticFeedback.lightImpact();
      setState(() => _resultado = Fmt.resultado(r));
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e is ApiException ? e.message : e.toString());
    } finally {
      if (mounted) setState(() => _ejecutando = false);
    }
  }

  Widget _campo(ParamInfo p) {
    switch (p.tipo) {
      case 'booleano':
        return SwitchListTile(
          contentPadding: EdgeInsets.zero,
          title: Text(p.etiqueta),
          value: _booleanos[p.nombre] ?? false,
          onChanged: (v) => setState(() => _booleanos[p.nombre] = v),
        );
      case 'fecha':
      case 'fechahora':
        return InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () async {
            final d = await showDatePicker(
              context: context,
              initialDate: _fechas[p.nombre] ?? DateTime.now(),
              firstDate: DateTime(1900),
              lastDate: DateTime(2100),
            );
            if (d != null) setState(() => _fechas[p.nombre] = d);
          },
          child: InputDecorator(
            decoration: InputDecoration(labelText: p.etiqueta, prefixIcon: const Icon(Icons.event_outlined)),
            child: Text(Fmt.fecha(_fechas[p.nombre])),
          ),
        );
      default:
        final numerico = p.tipo == 'entero' || p.tipo == 'decimal';
        return TextFormField(
          controller: _textos[p.nombre],
          decoration: InputDecoration(
            labelText: p.etiqueta,
            prefixIcon: Icon(numerico ? Icons.numbers_rounded : Icons.short_text_rounded),
          ),
          keyboardType: p.tipo == 'decimal'
              ? const TextInputType.numberWithOptions(decimal: true)
              : p.tipo == 'entero'
                  ? TextInputType.number
                  : TextInputType.text,
          validator: (v) {
            final t = (v ?? '').trim();
            if (t.isEmpty) return 'Completa ${p.etiqueta.toLowerCase()}';
            if (p.tipo == 'entero' && int.tryParse(t) == null) return 'Debe ser un número entero';
            if (p.tipo == 'decimal' && double.tryParse(t.replaceAll(',', '.')) == null) return 'Debe ser un número';
            return null;
          },
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textos = Theme.of(context).textTheme;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 0, 20, 20 + MediaQuery.of(context).viewInsets.bottom),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                IconBubble(icon: Icons.bolt_rounded, color: widget.color),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(widget.accion.etiqueta, style: textos.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
                      Text(
                        widget.accion.parametros.isEmpty ? 'No necesita datos' : 'Completa los datos y ejecuta',
                        style: textos.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            for (final p in widget.accion.parametros) ...[_campo(p), const SizedBox(height: 12)],
            FilledButton(
              onPressed: _ejecutando ? null : _ejecutar,
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 200),
                child: _ejecutando
                    ? const SizedBox(key: ValueKey('c'), width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.4))
                    : const Row(
                        key: ValueKey('t'),
                        mainAxisSize: MainAxisSize.min,
                        children: [Icon(Icons.play_arrow_rounded), SizedBox(width: 6), Text('Ejecutar')],
                      ),
              ),
            ),
            AnimatedSize(
              duration: const Duration(milliseconds: 260),
              curve: Curves.easeOutCubic,
              child: (_resultado == null && _error == null)
                  ? const SizedBox(width: double.infinity)
                  : Container(
                      width: double.infinity,
                      margin: const EdgeInsets.only(top: 16),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: _error != null ? scheme.errorContainer : scheme.primaryContainer,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _error != null ? 'No se pudo ejecutar' : 'Resultado',
                            style: textos.labelLarge?.copyWith(
                              color: _error != null ? scheme.onErrorContainer : scheme.onPrimaryContainer,
                            ),
                          ),
                          const SizedBox(height: 6),
                          SelectableText(
                            _error ?? _resultado!,
                            style: textos.titleMedium?.copyWith(
                              color: _error != null ? scheme.onErrorContainer : scheme.onPrimaryContainer,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
