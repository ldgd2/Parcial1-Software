import 'package:flutter/material.dart';

import '../../app/modulo.dart';
import '../../app/modulos.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/fmt.dart';
import '../../shared/widgets/animations.dart';
import '../../shared/widgets/entity_widgets.dart';
import '../../shared/widgets/state_views.dart';

/// Inicio: saludo, resumen con contadores, accesos rápidos y lo más reciente.
class DashboardView extends StatefulWidget {
  const DashboardView({super.key});

  @override
  State<DashboardView> createState() => _DashboardViewState();
}

class _DashboardViewState extends State<DashboardView> {
  List<int?> _conteos = List.filled(modulos.length, null);
  List<ResumenItem>? _recientes;
  bool _sinConexion = false;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<int> _contar(ModuloInfo m) async {
    try {
      return await m.contar();
    } catch (_) {
      return -1;
    }
  }

  Future<void> _cargar() async {
    final conteos = await Future.wait(modulos.map(_contar));
    List<ResumenItem> recientes = [];
    if (modulos.isNotEmpty) {
      try {
        recientes = await modulos.first.recientes();
      } catch (_) {}
    }
    if (!mounted) return;
    setState(() {
      _conteos = conteos;
      _recientes = recientes;
      _sinConexion = conteos.isNotEmpty && conteos.every((c) => c < 0);
    });
  }

  Future<void> _abrir(Widget Function() pagina) async {
    await Navigator.of(context).push(appRoute(pagina()));
    _cargar();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textos = Theme.of(context).textTheme;
    final ancho = MediaQuery.of(context).size.width;

    return RefreshIndicator(
      onRefresh: _cargar,
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(parent: BouncingScrollPhysics()),
        slivers: [
          SliverToBoxAdapter(child: _encabezado(context)),
          if (_sinConexion)
            SliverToBoxAdapter(
              child: FadeSlideIn(
                child: Container(
                  margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(color: scheme.errorContainer, borderRadius: BorderRadius.circular(16)),
                  child: Row(
                    children: [
                      Icon(Icons.cloud_off_rounded, color: scheme.onErrorContainer),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Sin conexión con el servidor. Revisa API_BASE_URL en el archivo .env',
                          style: TextStyle(color: scheme.onErrorContainer),
                        ),
                      ),
                      TextButton(onPressed: _cargar, child: const Text('Reintentar')),
                    ],
                  ),
                ),
              ),
            ),
          if (modulos.isEmpty)
            const SliverFillRemaining(
              hasScrollBody: false,
              child: EmptyState(
                icon: Icons.widgets_outlined,
                title: 'Sin módulos',
                message: 'El diagrama no tiene clases todavía.',
              ),
            )
          else ...[
            const SliverToBoxAdapter(child: SectionTitle('Resumen')),
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              sliver: SliverGrid(
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: ancho > 700 ? 4 : 2,
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: 1.35,
                ),
                delegate: SliverChildBuilderDelegate(
                  (context, i) => FadeSlideIn(index: i, child: _tarjetaConteo(modulos[i], _conteos[i])),
                  childCount: modulos.length,
                ),
              ),
            ),
            const SliverToBoxAdapter(child: SectionTitle('Accesos rápidos')),
            SliverToBoxAdapter(
              child: SizedBox(
                height: 48,
                child: ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  scrollDirection: Axis.horizontal,
                  itemCount: modulos.length,
                  separatorBuilder: (context, i) => const SizedBox(width: 8),
                  itemBuilder: (context, i) => FadeSlideIn(
                    index: i,
                    child: FilledButton.tonalIcon(
                      style: FilledButton.styleFrom(minimumSize: const Size(0, 44)),
                      onPressed: () => _abrir(modulos[i].nuevo),
                      icon: Icon(modulos[i].icono, size: 18),
                      label: Text('Nuevo ${modulos[i].nombre.toLowerCase()}'),
                    ),
                  ),
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: SectionTitle(
                'Recientes en ${modulos.first.plural.toLowerCase()}',
                trailing: TextButton(onPressed: () => _abrir(modulos.first.lista), child: const Text('Ver todo')),
              ),
            ),
            _seccionRecientes(textos, scheme),
            const SliverToBoxAdapter(child: SizedBox(height: 24)),
          ],
        ],
      ),
    );
  }

  Widget _encabezado(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textos = Theme.of(context).textTheme;
    return Container(
      padding: EdgeInsets.fromLTRB(20, MediaQuery.of(context).padding.top + 20, 20, 28),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [scheme.primary, Color.lerp(scheme.primary, scheme.tertiary, 0.7)!],
        ),
        borderRadius: const BorderRadius.vertical(bottom: Radius.circular(32)),
      ),
      child: FadeSlideIn(
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(Fmt.saludo(), style: textos.titleMedium?.copyWith(color: Colors.white.withAlpha(220))),
                  const SizedBox(height: 4),
                  Text(
                    '__APP_TITLE__',
                    style: textos.headlineSmall?.copyWith(color: Colors.white, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '__APP_SUBTITLE__',
                    style: textos.bodyMedium?.copyWith(color: Colors.white.withAlpha(210)),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(color: Colors.white.withAlpha(40), borderRadius: BorderRadius.circular(20)),
              child: const Center(child: PulseIcon(icon: __HERO_ICON__, color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _tarjetaConteo(ModuloInfo m, int? conteo) {
    final textos = Theme.of(context).textTheme;
    final scheme = Theme.of(context).colorScheme;
    return PressableScale(
      child: Material(
        color: AppTheme.tarjeta(context),
        borderRadius: BorderRadius.circular(20),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: () => _abrir(m.lista),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                IconBubble(icon: m.icono, color: m.color, size: 40),
                const Spacer(),
                if (conteo == null)
                  const SizedBox(height: 30, width: 30, child: CircularProgressIndicator(strokeWidth: 2.4))
                else if (conteo < 0)
                  Text('—', style: textos.headlineSmall?.copyWith(fontWeight: FontWeight.w800))
                else
                  AnimatedCounter(value: conteo, style: textos.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
                Text(
                  m.plural,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: textos.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _seccionRecientes(TextTheme textos, ColorScheme scheme) {
    final recientes = _recientes;
    if (recientes == null) return const SliverToBoxAdapter(child: SkeletonList(count: 3));
    if (recientes.isEmpty) {
      return SliverToBoxAdapter(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Text(
            _sinConexion ? 'No se pudieron cargar los datos.' : 'Todavía no hay registros. ¡Crea el primero!',
            style: textos.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
          ),
        ),
      );
    }
    final m = modulos.first;
    return SliverList.builder(
      itemCount: recientes.length,
      itemBuilder: (context, i) => FadeSlideIn(
        index: i,
        child: Container(
          margin: const EdgeInsets.fromLTRB(16, 0, 16, 10),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: AppTheme.tarjeta(context), borderRadius: BorderRadius.circular(18)),
          child: Row(
            children: [
              EntityAvatar(text: recientes[i].titulo, color: m.color, size: 42),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(recientes[i].titulo, maxLines: 1, overflow: TextOverflow.ellipsis, style: textos.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
                    if (recientes[i].subtitulo.isNotEmpty)
                      Text(recientes[i].subtitulo, maxLines: 1, overflow: TextOverflow.ellipsis, style: textos.bodySmall?.copyWith(color: scheme.onSurfaceVariant)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
