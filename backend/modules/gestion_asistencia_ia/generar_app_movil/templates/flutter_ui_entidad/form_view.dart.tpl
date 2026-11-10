import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/network/api_client.dart';
import '../../core/utils/fmt.dart';
import '../../models/__SNAKE__.dart';
import '../../services/__SNAKE___service.dart';
import '../../shared/widgets/animations.dart';
import '../../shared/widgets/entity_widgets.dart';
import '__SNAKE___ui.dart';

class __PASCAL__FormView extends StatefulWidget {
  final __PASCAL__? item;
  const __PASCAL__FormView({super.key, this.item});

  @override
  State<__PASCAL__FormView> createState() => ___PASCAL__FormViewState();
}

class ___PASCAL__FormViewState extends State<__PASCAL__FormView> {
  final _formKey = GlobalKey<FormState>();
  final __PASCAL__Service _service = __PASCAL__Service();
  bool _guardando = false;

__DECLARACIONES__

  bool get _editando => widget.item != null;

  @override
  void initState() {
    super.initState();
    final item = widget.item;
    if (item != null) {
__INICIALES__
    }
  }

  @override
  void dispose() {
__DISPOSE__
    super.dispose();
  }

  Future<void> _elegirFecha(DateTime? actual, ValueChanged<DateTime> elegir) async {
    final d = await showDatePicker(
      context: context,
      initialDate: actual ?? DateTime.now(),
      firstDate: DateTime(1900),
      lastDate: DateTime(2100),
    );
    if (d != null) setState(() => elegir(d));
  }

  Future<void> _guardar() async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) {
      HapticFeedback.mediumImpact();
      return;
    }
    setState(() => _guardando = true);
    final datos = <String, dynamic>{
__PAYLOAD__
    };
    try {
      if (_editando) {
        await _service.update(widget.item!.id, datos);
      } else {
        await _service.create(datos);
      }
      HapticFeedback.lightImpact();
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _guardando = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e is ApiException ? e.message : 'No se pudo guardar: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textos = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: Text(_editando ? 'Editar __NOMBRE_MIN__' : 'Nuevo __NOMBRE_MIN__')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            FadeSlideIn(
              child: Row(
                children: [
                  const IconBubble(icon: __PASCAL__Ui.icono, color: __PASCAL__Ui.color, size: 52),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Text(
                      _editando ? 'Actualiza los datos y guarda los cambios.' : 'Completa los datos del nuevo registro.',
                      style: textos.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
__CAMPOS__
          ],
        ),
      ),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.fromLTRB(16, 8, 16, 12),
        child: FilledButton(
          onPressed: _guardando ? null : _guardar,
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 220),
            child: _guardando
                ? const SizedBox(key: ValueKey('g'), width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.4))
                : Row(
                    key: const ValueKey('t'),
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.check_rounded),
                      const SizedBox(width: 8),
                      Text(_editando ? 'Guardar cambios' : 'Crear __NOMBRE_MIN__'),
                    ],
                  ),
          ),
        ),
      ),
    );
  }
}
