import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../custom_animation.dart';

/// Extensiones para animaciones basadas en interacción del usuario (tap, hover)
extension CustomInteractionAnimation on Widget {
  
  /// Animación de Hover / Foco (Elevar y escalar ligeramente).
  /// Ideal para tarjetas o botones cuando son enfocados (útil en Web/Desktop o al tocar en móvil).
  Animate animarFoco({bool enfocado = true}) {
    return animate(target: enfocado ? 1 : 0)
        .scale(
          end: const Offset(1.02, 1.02), 
          duration: CustomAnimConfig.rapido, 
          curve: CustomAnimConfig.curvaEntrada
        )
        .moveY(end: -4, duration: CustomAnimConfig.rapido);
  }

  /// Animación de Presión (Shrink / Hundir).
  /// Útil para dar feedback inmediato al presionar un botón o tarjeta.
  Animate animarPresion({bool presionado = true}) {
    return animate(target: presionado ? 1 : 0)
        .scale(
          end: const Offset(0.95, 0.95), 
          duration: const Duration(milliseconds: 100), 
          curve: Curves.easeOut
        );
  }
}
