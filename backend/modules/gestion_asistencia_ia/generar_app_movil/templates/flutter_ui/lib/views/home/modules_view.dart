import 'package:flutter/material.dart';

import '../../app/modulo.dart';
import '../../app/modulos.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/widgets/animations.dart';
import '../../shared/widgets/entity_widgets.dart';

/// Todos los módulos de la app en una cuadrícula.
class ModulesView extends StatelessWidget {
  const ModulesView({super.key});

  @override
  Widget build(BuildContext context) {
    final ancho = MediaQuery.of(context).size.width;
    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        const SliverAppBar.large(title: Text('Módulos')),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
          sliver: SliverGrid(
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: ancho > 700 ? 3 : 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 0.92,
            ),
            delegate: SliverChildBuilderDelegate(
              (context, i) => FadeSlideIn(index: i, child: _TarjetaModulo(modulo: modulos[i])),
              childCount: modulos.length,
            ),
          ),
        ),
      ],
    );
  }
}

class _TarjetaModulo extends StatelessWidget {
  final ModuloInfo modulo;
  const _TarjetaModulo({required this.modulo});

  @override
  Widget build(BuildContext context) {
    final textos = Theme.of(context).textTheme;
    final scheme = Theme.of(context).colorScheme;
    return PressableScale(
      child: Material(
        color: AppTheme.tarjeta(context),
        borderRadius: BorderRadius.circular(22),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: () => Navigator.of(context).push(appRoute(modulo.lista())),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [modulo.color.withAlpha(30), Colors.transparent],
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                IconBubble(icon: modulo.icono, color: modulo.color, size: 48),
                const Spacer(),
                Text(modulo.plural, style: textos.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 4),
                Text(
                  modulo.descripcion,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: textos.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                ),
                if (modulo.acciones.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  InfoChip(
                    label: '${modulo.acciones.length} ${modulo.acciones.length == 1 ? 'acción' : 'acciones'}',
                    icon: Icons.bolt_rounded,
                    color: modulo.color,
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
