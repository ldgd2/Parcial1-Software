import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_spinner.dart';

/// Un envoltorio (Wrapper) que coloca una pantalla de carga encima de cualquier widget.
/// Ideal para bloquear la pantalla completa o una tarjeta mientras se ejecuta una acción asíncrona.
class CustomLoaderOverlay extends StatelessWidget {
  final Widget child;
  final bool isLoading;
  final String? loadingText;
  final Widget? customLoader;
  final Color? overlayColor;

  const CustomLoaderOverlay({
    super.key,
    required this.child,
    this.isLoading = false,
    this.loadingText,
    this.customLoader,
    this.overlayColor,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final textos = context.textos;

    return Stack(
      children: [
        // Widget base
        child,
        
        // Capa de bloqueo y carga
        if (isLoading)
          Positioned.fill(
            child: Container(
              color: overlayColor ?? themeColores.fondo.withValues(alpha: 0.7),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    customLoader ?? const CustomSpinner(),
                    if (loadingText != null) ...[
                      const SizedBox(height: 16),
                      Text(
                        loadingText!,
                        style: textos.cuerpoPequeno.copyWith(fontWeight: FontWeight.bold),
                      ).animate(onPlay: (c) => c.repeat(reverse: true)).fade(begin: 0.4, end: 1.0),
                    ]
                  ],
                ),
              ),
            ).animate().fadeIn(duration: 200.ms),
          ),
      ],
    );
  }
}
