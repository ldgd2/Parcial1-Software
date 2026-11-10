import 'package:flutter/material.dart';

import '../../app/modulos.dart';
import '../../core/config/api_config.dart';
import '../../core/network/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/theme/theme_controller.dart';
import '../../shared/widgets/animations.dart';
import '../../shared/widgets/entity_widgets.dart';
import '../../shared/widgets/state_views.dart';

/// Ajustes: tema, conexión con el servidor y acerca de.
class SettingsView extends StatefulWidget {
  const SettingsView({super.key});

  @override
  State<SettingsView> createState() => _SettingsViewState();
}

class _SettingsViewState extends State<SettingsView> {
  bool _probando = false;
  String? _estado;
  bool _ok = false;

  Future<void> _probar() async {
    setState(() {
      _probando = true;
      _estado = null;
    });
    try {
      if (modulos.isNotEmpty) await modulos.first.contar();
      _ok = true;
      _estado = 'Conectado correctamente';
    } catch (e) {
      _ok = false;
      _estado = e is ApiException ? e.message : e.toString();
    }
    if (mounted) setState(() => _probando = false);
  }

  Widget _tarjeta(BuildContext context, int index, Widget child) => FadeSlideIn(
        index: index,
        child: Container(
          margin: const EdgeInsets.fromLTRB(16, 0, 16, 8),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: AppTheme.tarjeta(context), borderRadius: BorderRadius.circular(20)),
          child: child,
        ),
      );

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textos = Theme.of(context).textTheme;
    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        const SliverAppBar.large(title: Text('Ajustes')),
        const SliverToBoxAdapter(child: SectionTitle('Apariencia')),
        SliverToBoxAdapter(
          child: _tarjeta(
            context,
            0,
            ValueListenableBuilder<ThemeMode>(
              valueListenable: temaApp,
              builder: (context, modo, _) => SegmentedButton<ThemeMode>(
                segments: const [
                  ButtonSegment(value: ThemeMode.system, icon: Icon(Icons.brightness_auto_rounded), label: Text('Sistema')),
                  ButtonSegment(value: ThemeMode.light, icon: Icon(Icons.light_mode_rounded), label: Text('Claro')),
                  ButtonSegment(value: ThemeMode.dark, icon: Icon(Icons.dark_mode_rounded), label: Text('Oscuro')),
                ],
                selected: {modo},
                onSelectionChanged: (s) => temaApp.value = s.first,
              ),
            ),
          ),
        ),
        const SliverToBoxAdapter(child: SectionTitle('Conexión')),
        SliverToBoxAdapter(
          child: _tarjeta(
            context,
            1,
            Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    IconBubble(icon: Icons.dns_rounded, color: scheme.primary, size: 40),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Servidor (API_BASE_URL)', style: textos.labelMedium?.copyWith(color: scheme.onSurfaceVariant)),
                          SelectableText(ApiConfig.baseUrl, style: textos.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  'Para cambiarlo edita el archivo .env de la app y vuelve a ejecutarla.',
                  style: textos.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
                ),
                const SizedBox(height: 12),
                FilledButton.tonalIcon(
                  onPressed: _probando ? null : _probar,
                  icon: _probando
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.wifi_tethering_rounded),
                  label: const Text('Probar conexión'),
                ),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 250),
                  child: _estado == null
                      ? const SizedBox.shrink()
                      : Padding(
                          key: ValueKey(_estado),
                          padding: const EdgeInsets.only(top: 12),
                          child: Row(
                            children: [
                              Icon(_ok ? Icons.check_circle_rounded : Icons.error_rounded, color: _ok ? Colors.green : scheme.error),
                              const SizedBox(width: 8),
                              Expanded(child: Text(_estado!)),
                            ],
                          ),
                        ),
                ),
              ],
            ),
          ),
        ),
        const SliverToBoxAdapter(child: SectionTitle('Acerca de')),
        SliverToBoxAdapter(
          child: _tarjeta(
            context,
            2,
            Row(
              children: [
                IconBubble(icon: __HERO_ICON__, color: scheme.primary, size: 40),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('__APP_TITLE__', style: textos.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
                      Text('Versión 1.0.0 · ${modulos.length} módulos', style: textos.bodySmall?.copyWith(color: scheme.onSurfaceVariant)),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SliverToBoxAdapter(child: SizedBox(height: 24)),
      ],
    );
  }
}
