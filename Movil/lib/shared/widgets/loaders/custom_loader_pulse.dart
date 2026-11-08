import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Indicador de carga tipo Radar / Pulso.
/// Ideal para búsqueda de dispositivos (Bluetooth, GPS), "Buscando conductor", etc.
class CustomLoaderPulse extends StatelessWidget {
  final double size;
  final Color? color;

  const CustomLoaderPulse({
    super.key,
    this.size = 60.0,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final themeColor = color ?? context.colores.primario;

    return Stack(
      alignment: Alignment.center,
      children: [
        // Círculo base estático
        Container(
          width: size * 0.25,
          height: size * 0.25,
          decoration: BoxDecoration(
            color: themeColor,
            shape: BoxShape.circle,
          ),
        ),
        // Círculo que se expande y difumina (Radar 1)
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            border: Border.all(color: themeColor.withValues(alpha: 0.5), width: 2),
            shape: BoxShape.circle,
          ),
        ).animate(onPlay: (c) => c.repeat())
         .scale(begin: const Offset(0.25, 0.25), end: const Offset(1.0, 1.0), duration: 1500.ms, curve: Curves.easeOut)
         .fadeOut(duration: 1500.ms),
         
        // Círculo que se expande y difumina (Radar 2) con retraso
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            border: Border.all(color: themeColor.withValues(alpha: 0.5), width: 2),
            shape: BoxShape.circle,
          ),
        ).animate(onPlay: (c) => c.repeat(), delay: 750.ms)
         .scale(begin: const Offset(0.25, 0.25), end: const Offset(1.0, 1.0), duration: 1500.ms, curve: Curves.easeOut)
         .fadeOut(duration: 1500.ms),
      ],
    );
  }
}
