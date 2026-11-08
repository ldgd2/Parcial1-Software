import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Indicador de carga abstracto de 3 puntos (Dots Loader).
/// Ideal para chats ("escribiendo..."), botones o cargas sutiles.
class CustomLoaderDots extends StatelessWidget {
  final double size;
  final Color? color;
  final Duration duration;

  const CustomLoaderDots({
    super.key,
    this.size = 8.0,
    this.color,
    this.duration = const Duration(milliseconds: 600),
  });

  @override
  Widget build(BuildContext context) {
    final themeColor = color ?? context.colores.secundario;

    return Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (index) {
        return Container(
          width: size,
          height: size,
          margin: const EdgeInsets.symmetric(horizontal: 4),
          decoration: BoxDecoration(
            color: themeColor,
            shape: BoxShape.circle,
          ),
        ).animate(
          onPlay: (controller) => controller.repeat(reverse: true),
          delay: Duration(milliseconds: 150 * index), // Cascada
        ).scale(
          begin: const Offset(0.5, 0.5), 
          end: const Offset(1.2, 1.2),
          duration: duration,
          curve: Curves.easeInOut,
        ).fade(
          begin: 0.3, 
          end: 1.0, 
          duration: duration,
        );
      }),
    );
  }
}
