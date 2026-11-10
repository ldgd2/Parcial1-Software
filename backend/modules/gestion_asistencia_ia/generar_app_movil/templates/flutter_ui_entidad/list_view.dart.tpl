import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../models/__SNAKE__.dart';
import '../../services/__SNAKE___service.dart';
import '../../shared/widgets/action_sheet.dart';
import '../../shared/widgets/animations.dart';
import '../../shared/widgets/entity_widgets.dart';
import '../../shared/widgets/state_views.dart';
import '__SNAKE___detail_view.dart';
import '__SNAKE___form_view.dart';
import '__SNAKE___ui.dart';

class __PASCAL__ListView extends StatefulWidget {
  const __PASCAL__ListView({super.key});

  @override
  State<__PASCAL__ListView> createState() => ___PASCAL__ListViewState();
}

class ___PASCAL__ListViewState extends State<__PASCAL__ListView> {
  final __PASCAL__Service _service = __PASCAL__Service();
  List<__PASCAL__> _items = [];
  bool _cargando = true;
  String? _error;
  String _busqueda = '';
  bool _fabExtendido = true;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = _items.isEmpty;
      _error = null;
    });
    try {
      final datos = await _service.getAll();
      if (!mounted) return;
      setState(() {
        _items = datos;
        _cargando = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e is ApiException ? e.message : e.toString();
        _cargando = false;
      });
    }
  }

  void _aviso(String texto) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(texto)));
  }

  Future<void> _nuevo() async {
    final creado = await Navigator.of(context).push<bool>(appRoute(const __PASCAL__FormView()));
    if (creado == true) {
      _aviso('__NOMBRE__ creado');
      _cargar();
    }
  }

  Future<void> _abrir(__PASCAL__ item) async {
    final cambio = await Navigator.of(context).push<bool>(appRoute(__PASCAL__DetailView(item: item)));
    if (cambio == true) _cargar();
  }

  Future<bool> _eliminar(__PASCAL__ item) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.delete_outline_rounded),
        title: const Text('¿Eliminar registro?'),
        content: Text('Se eliminará «${__PASCAL__Ui.titulo(item)}». Esta acción no se puede deshacer.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Eliminar')),
        ],
      ),
    );
    if (ok != true) return false;
    try {
      await _service.delete(item.id);
      if (!mounted) return true;
      setState(() => _items.removeWhere((e) => e.id == item.id));
      _aviso('Registro eliminado');
      return true;
    } catch (e) {
      _aviso(e is ApiException ? e.message : 'No se pudo eliminar');
      return false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final acciones = __PASCAL__Ui.acciones(_service);
    final q = _busqueda.trim().toLowerCase();
    final visibles = q.isEmpty ? _items : _items.where((e) => __PASCAL__Ui.coincide(e, q)).toList();

    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _nuevo,
        isExtended: _fabExtendido,
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nuevo'),
      ),
      body: NotificationListener<UserScrollNotification>(
        onNotification: (n) {
          final extendido = n.direction != ScrollDirection.reverse;
          if (extendido != _fabExtendido) setState(() => _fabExtendido = extendido);
          return false;
        },
        child: RefreshIndicator(
          onRefresh: _cargar,
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(parent: BouncingScrollPhysics()),
            slivers: [
              SliverAppBar.medium(
                title: const Text(__PASCAL__Ui.plural),
                actions: [IconButton(onPressed: _cargar, icon: const Icon(Icons.refresh_rounded), tooltip: 'Actualizar')],
              ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                  child: TextField(
                    onChanged: (v) => setState(() => _busqueda = v),
                    decoration: InputDecoration(
                      hintText: 'Buscar en ${__PASCAL__Ui.plural.toLowerCase()}',
                      prefixIcon: const Icon(Icons.search_rounded),
                    ),
                  ),
                ),
              ),
              if (acciones.isNotEmpty)
                SliverToBoxAdapter(
                  child: SizedBox(
                    height: 48,
                    child: ListView.separated(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                      scrollDirection: Axis.horizontal,
                      itemCount: acciones.length,
                      separatorBuilder: (context, i) => const SizedBox(width: 8),
                      itemBuilder: (context, i) => ActionChip(
                        avatar: const Icon(Icons.bolt_rounded, size: 18, color: __PASCAL__Ui.color),
                        label: Text(acciones[i].etiqueta),
                        onPressed: () => mostrarAccion(context, acciones[i], __PASCAL__Ui.color),
                      ),
                    ),
                  ),
                ),
              ..._contenido(visibles),
              const SliverToBoxAdapter(child: SizedBox(height: 96)),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _contenido(List<__PASCAL__> visibles) {
    if (_cargando) return const [SliverToBoxAdapter(child: SkeletonList())];
    if (_error != null) {
      return [SliverFillRemaining(hasScrollBody: false, child: ErrorState(message: _error!, onRetry: _cargar))];
    }
    if (visibles.isEmpty) {
      return [
        SliverFillRemaining(
          hasScrollBody: false,
          child: _busqueda.isNotEmpty
              ? const EmptyState(
                  icon: Icons.search_off_rounded,
                  title: 'Sin resultados',
                  message: 'Prueba con otras palabras.',
                )
              : EmptyState(
                  icon: __PASCAL__Ui.icono,
                  title: 'Aún no hay ${__PASCAL__Ui.plural.toLowerCase()}',
                  message: 'Crea el primer registro para empezar.',
                  actionLabel: 'Crear ${__PASCAL__Ui.nombre.toLowerCase()}',
                  onAction: _nuevo,
                ),
        ),
      ];
    }
    return [
      SliverList.builder(
        itemCount: visibles.length,
        itemBuilder: (context, i) => FadeSlideIn(index: i, child: _tarjeta(visibles[i])),
      ),
    ];
  }

  Widget _tarjeta(__PASCAL__ item) {
    final scheme = Theme.of(context).colorScheme;
    final textos = Theme.of(context).textTheme;
    final titulo = __PASCAL__Ui.titulo(item);
    final subtitulo = __PASCAL__Ui.subtitulo(item);
    final destacados = __PASCAL__Ui.destacados(item);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
      child: Dismissible(
        key: ValueKey(item.id),
        direction: DismissDirection.endToStart,
        confirmDismiss: (_) => _eliminar(item),
        background: Container(
          alignment: Alignment.centerRight,
          padding: const EdgeInsets.only(right: 24),
          decoration: BoxDecoration(color: scheme.errorContainer, borderRadius: BorderRadius.circular(20)),
          child: Icon(Icons.delete_outline_rounded, color: scheme.onErrorContainer),
        ),
        child: PressableScale(
          child: Material(
            color: AppTheme.tarjeta(context),
            borderRadius: BorderRadius.circular(20),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: () => _abrir(item),
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    EntityAvatar(text: titulo, color: __PASCAL__Ui.color, heroTag: '__SNAKE__-${item.id}'),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(titulo, maxLines: 1, overflow: TextOverflow.ellipsis, style: textos.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                          if (subtitulo.isNotEmpty)
                            Text(subtitulo, maxLines: 1, overflow: TextOverflow.ellipsis, style: textos.bodySmall?.copyWith(color: scheme.onSurfaceVariant)),
                          if (destacados.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            Wrap(
                              spacing: 6,
                              runSpacing: 6,
                              children: [for (final d in destacados) InfoChip(label: d.valor, icon: d.icono, color: __PASCAL__Ui.color)],
                            ),
                          ],
                        ],
                      ),
                    ),
                    Icon(Icons.chevron_right_rounded, color: scheme.onSurfaceVariant),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
