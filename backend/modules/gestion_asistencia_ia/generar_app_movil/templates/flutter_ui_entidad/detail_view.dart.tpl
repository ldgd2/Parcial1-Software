import 'package:flutter/material.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../models/__SNAKE__.dart';
import '../../services/__SNAKE___service.dart';
import '../../shared/widgets/action_sheet.dart';
import '../../shared/widgets/animations.dart';
import '../../shared/widgets/entity_widgets.dart';
import '../../shared/widgets/state_views.dart';
import '__SNAKE___form_view.dart';
import '__SNAKE___ui.dart';

class __PASCAL__DetailView extends StatefulWidget {
  final __PASCAL__ item;
  const __PASCAL__DetailView({super.key, required this.item});

  @override
  State<__PASCAL__DetailView> createState() => ___PASCAL__DetailViewState();
}

class ___PASCAL__DetailViewState extends State<__PASCAL__DetailView> {
  final __PASCAL__Service _service = __PASCAL__Service();
  late __PASCAL__ _item = widget.item;
  bool _cambio = false;

  void _aviso(String texto) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(texto)));
  }

  Future<void> _editar() async {
    final guardado = await Navigator.of(context).push<bool>(appRoute(__PASCAL__FormView(item: _item)));
    if (guardado != true) return;
    _cambio = true;
    try {
      final actualizado = await _service.getById(_item.id);
      if (mounted) setState(() => _item = actualizado);
    } catch (_) {}
    _aviso('Cambios guardados');
  }

  Future<void> _eliminar() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.delete_outline_rounded),
        title: const Text('¿Eliminar registro?'),
        content: const Text('Esta acción no se puede deshacer.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Eliminar')),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await _service.delete(_item.id);
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      _aviso(e is ApiException ? e.message : 'No se pudo eliminar');
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textos = Theme.of(context).textTheme;
    const color = __PASCAL__Ui.color;
    final campos = __PASCAL__Ui.campos(_item);
    final acciones = __PASCAL__Ui.acciones(_service);
    final titulo = __PASCAL__Ui.titulo(_item);

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) Navigator.of(context).pop(_cambio);
      },
      child: Scaffold(
        body: CustomScrollView(
          physics: const BouncingScrollPhysics(),
          slivers: [
            SliverAppBar(
              pinned: true,
              stretch: true,
              expandedHeight: 250,
              backgroundColor: color,
              foregroundColor: Colors.white,
              flexibleSpace: FlexibleSpaceBar(
                title: Text(titulo, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                background: Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [color, Color.lerp(color, Colors.black, 0.35)!],
                    ),
                  ),
                  child: SafeArea(
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 56),
                      child: Center(
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: Colors.white.withAlpha(150), width: 2)),
                          child: EntityAvatar(text: titulo, color: color, size: 88, heroTag: '__SNAKE__-${_item.id}'),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            const SliverToBoxAdapter(child: SectionTitle('Información')),
            SliverList.builder(
              itemCount: campos.length,
              itemBuilder: (context, i) => FadeSlideIn(
                index: i,
                child: Container(
                  margin: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(color: AppTheme.tarjeta(context), borderRadius: BorderRadius.circular(16)),
                  child: Row(
                    children: [
                      IconBubble(icon: campos[i].icono, color: color, size: 40),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(campos[i].etiqueta, style: textos.labelMedium?.copyWith(color: scheme.onSurfaceVariant)),
                            const SizedBox(height: 2),
                            SelectableText(campos[i].valor, style: textos.bodyLarge?.copyWith(fontWeight: FontWeight.w600)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            if (acciones.isNotEmpty) ...[
              const SliverToBoxAdapter(child: SectionTitle('Acciones')),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final a in acciones)
                        ActionChip(
                          avatar: const Icon(Icons.bolt_rounded, size: 18, color: color),
                          label: Text(a.etiqueta),
                          onPressed: () => mostrarAccion(context, a, color),
                        ),
                    ],
                  ),
                ),
              ),
            ],
            const SliverToBoxAdapter(child: SizedBox(height: 24)),
          ],
        ),
        bottomNavigationBar: SafeArea(
          minimum: const EdgeInsets.fromLTRB(16, 8, 16, 12),
          child: Row(
            children: [
              Expanded(
                flex: 2,
                child: OutlinedButton.icon(
                  onPressed: _eliminar,
                  style: OutlinedButton.styleFrom(foregroundColor: scheme.error),
                  icon: const Icon(Icons.delete_outline_rounded),
                  label: const Text('Eliminar'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 3,
                child: FilledButton.icon(
                  onPressed: _editar,
                  icon: const Icon(Icons.edit_rounded),
                  label: const Text('Editar'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
