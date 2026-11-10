import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import 'animations.dart';

/// Tarjetas "fantasma" mientras llegan los datos.
class SkeletonList extends StatelessWidget {
  final int count;
  const SkeletonList({super.key, this.count = 6});

  @override
  Widget build(BuildContext context) {
    final bloque = Theme.of(context).colorScheme.surfaceContainerHighest;
    Widget barra(double ancho, double alto) => Container(
          width: ancho,
          height: alto,
          decoration: BoxDecoration(color: bloque, borderRadius: BorderRadius.circular(8)),
        );
    return Shimmer(
      child: Column(
        children: List.generate(
          count,
          (i) => Container(
            margin: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.tarjeta(context),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              children: [
                Container(width: 48, height: 48, decoration: BoxDecoration(color: bloque, shape: BoxShape.circle)),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [barra(160, 14), const SizedBox(height: 8), barra(100, 12)],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Estado vacío con ilustración animada y acción opcional.
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textos = Theme.of(context).textTheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: FadeSlideIn(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 104,
                height: 104,
                decoration: BoxDecoration(color: scheme.primaryContainer, shape: BoxShape.circle),
                child: Center(child: PulseIcon(icon: icon, size: 46, color: scheme.onPrimaryContainer)),
              ),
              const SizedBox(height: 20),
              Text(title, style: textos.titleLarge?.copyWith(fontWeight: FontWeight.w700), textAlign: TextAlign.center),
              const SizedBox(height: 8),
              Text(message, style: textos.bodyMedium?.copyWith(color: scheme.onSurfaceVariant), textAlign: TextAlign.center),
              if (actionLabel != null && onAction != null) ...[
                const SizedBox(height: 20),
                FilledButton.icon(onPressed: onAction, icon: const Icon(Icons.add_rounded), label: Text(actionLabel!)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Error de conexión con opción de reintentar.
class ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const ErrorState({super.key, required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textos = Theme.of(context).textTheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: FadeSlideIn(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 96,
                height: 96,
                decoration: BoxDecoration(color: scheme.errorContainer, shape: BoxShape.circle),
                child: Icon(Icons.cloud_off_rounded, size: 44, color: scheme.onErrorContainer),
              ),
              const SizedBox(height: 20),
              Text('Algo salió mal', style: textos.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              Text(message, style: textos.bodyMedium?.copyWith(color: scheme.onSurfaceVariant), textAlign: TextAlign.center),
              const SizedBox(height: 20),
              FilledButton.tonalIcon(onPressed: onRetry, icon: const Icon(Icons.refresh_rounded), label: const Text('Reintentar')),
            ],
          ),
        ),
      ),
    );
  }
}

/// Título de sección.
class SectionTitle extends StatelessWidget {
  final String text;
  final Widget? trailing;
  const SectionTitle(this.text, {super.key, this.trailing});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 24, 16, 12),
      child: Row(
        children: [
          Expanded(
            child: Text(text, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}
