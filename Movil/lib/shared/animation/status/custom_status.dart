import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../custom_animation.dart';

/// Extensiones para animaciones de estado (carga, éxito, información)
extension CustomStatusAnimation on Widget {
  
  /// Efecto esqueleto de carga (Shimmer).
  /// Muestra un barrido de luz indicando que el componente está cargando datos.
  Animate animarCarga({bool isLoading = true, Color? shimmerColor}) {
    if (!isLoading) return animate();
    // Reemplazamos shimmer por un pulso de opacidad (fade) que es 100% infalible en todos los contenedores y luce como el estándar de iOS.
    return animate(onPlay: (controller) => controller.repeat(reverse: true))
        .fade(begin: 0.4, end: 1.0, duration: const Duration(milliseconds: 1000));
  }

  /// Destello de éxito (Verde).
  /// Útil para confirmar visualmente que algo guardó o se completó con éxito.
  Animate animarExito({bool activar = true}) {
    return animate(target: activar ? 1 : 0)
        .tint(color: Colors.greenAccent.withAlpha(150), end: 0.5, duration: CustomAnimConfig.rapido)
        .then()
        .tint(color: Colors.transparent, duration: CustomAnimConfig.rapido);
  }

  /// Destello general de actualización (Blanco/Neutro).
  Animate animarDestello({bool activar = true}) {
    return animate(target: activar ? 1 : 0)
        .tint(color: Colors.white, end: 0.5, duration: CustomAnimConfig.rapido)
        .then()
        .tint(color: Colors.transparent, duration: CustomAnimConfig.rapido);
  }
}
