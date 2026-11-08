import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Indicador de carga tipo Olas / Ecualizador (Wave / Bars).
/// Ideal para simular procesamiento de audio, análisis de datos o cargas intensas.
class CustomLoaderWave extends StatelessWidget {
  final double width;
  final double height;
  final Color? color;
  final int barsCount;
  final Duration duration;

  const CustomLoaderWave({
    super.key,
    this.width = 4.0,
    this.height = 24.0,
    this.color,
    this.barsCount = 5,
    this.duration = const Duration(milliseconds: 500),
  });

  @override
  Widget build(BuildContext context) {
    final themeColor = color ?? context.colores.primario;

    return Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: List.generate(barsCount, (index) {
        return Container(
          width: width,
          height: height,
          margin: const EdgeInsets.symmetric(horizontal: 3),
          decoration: BoxDecoration(
            color: themeColor,
            borderRadius: BorderRadius.circular(width),
          ),
        ).animate(
          onPlay: (controller) => controller.repeat(reverse: true),
          delay: Duration(milliseconds: (index * 100)), // Efecto ola secuencial
        ).scaleY(
          begin: 0.3,
          end: 1.0,
          curve: Curves.easeInOutCubic,
          duration: duration,
        );
      }),
    );
  }
}
