import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../custom_animation.dart';

/// Extensiones para animaciones de advertencia, errores o alertas
extension CustomWarningAnimation on Widget {
  
  /// Animación de atención (Agitación/Shake).
  /// Ideal para indicar validaciones fallidas en Inputs, contraseñas incorrectas o errores.
  /// Si `activar` es true, lanza la animación.
  Animate animarError({bool activar = true}) {
    return animate(target: activar ? 1 : 0)
        .shake(
          hz: 4, 
          curve: Curves.easeInOutCubic, 
          duration: CustomAnimConfig.normal,
        )
        .tint(color: Colors.redAccent, end: 0.2, duration: CustomAnimConfig.rapido)
        .then()
        .tint(color: Colors.transparent, duration: CustomAnimConfig.rapido);
  }

  /// Animación de latido constante (Pulse).
  /// Ideal para alertas urgentes, llamadas a la acción, o notificaciones importantes.
  Animate animarLatido({bool activar = true}) {
    if (!activar) return animate();
    return animate(onPlay: (controller) => controller.repeat(reverse: true))
        .scale(
          begin: const Offset(1.0, 1.0),
          end: const Offset(1.06, 1.06),
          duration: CustomAnimConfig.normal,
          curve: CustomAnimConfig.curvaSuave,
        );
  }

  /// Destello rápido (Flash) rojo/naranja.
  /// Útil para advertir que una acción destructiva está a punto de ocurrir.
  Animate animarDestelloPeligro({bool activar = true}) {
    return animate(target: activar ? 1 : 0)
        .tint(color: Colors.orangeAccent, end: 0.5, duration: CustomAnimConfig.rapido)
        .then()
        .tint(color: Colors.transparent, duration: CustomAnimConfig.rapido);
  }
}
