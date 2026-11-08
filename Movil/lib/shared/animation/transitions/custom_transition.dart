import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../custom_animation.dart';

/// Extensiones para animaciones de transición (entradas y salidas)
extension CustomTransitionAnimation on Widget {
  
  /// Animación "Hero" nativa de Flutter.
  /// Convierte el Widget en un elemento que "vuela" suavemente entre pantallas.
  /// Ideal para imágenes o avatares en listas que se expanden a detalle.
  Widget animarHero(String tag) {
    return Hero(
      tag: tag,
      child: this,
    );
  }

  /// Animación de entrada estándar (Fade In + Deslizamiento suave hacia arriba).
  /// Ideal para Cards, ListTiles, textos y elementos que aparecen al cargar la pantalla.
  Animate animarEntrada({Duration? delay, Duration? duracion, Offset beginOffset = const Offset(0, 0.1)}) {
    return animate(delay: delay)
        .fadeIn(duration: duracion ?? CustomAnimConfig.normal, curve: CustomAnimConfig.curvaEntrada)
        .slide(
          begin: beginOffset, 
          end: Offset.zero, 
          duration: duracion ?? CustomAnimConfig.normal, 
          curve: CustomAnimConfig.curvaEntrada,
        );
  }

  /// Animación de entrada con un rebote (Pop/Scale).
  /// Ideal para diálogos, botones flotantes, badges o alertas.
  Animate animarRebote({Duration? delay}) {
    return animate(delay: delay)
        .scale(
          begin: const Offset(0.7, 0.7), 
          end: const Offset(1.0, 1.0),
          duration: CustomAnimConfig.normal,
          curve: CustomAnimConfig.curvaRebote,
        )
        .fadeIn(duration: CustomAnimConfig.rapido);
  }
  
  /// Animación de salida estándar (Fade Out + Deslizamiento hacia abajo).
  Animate animarSalida({bool activar = true}) {
    return animate(target: activar ? 1 : 0)
        .fadeOut(duration: CustomAnimConfig.rapido, curve: CustomAnimConfig.curvaSalida)
        .slide(
          begin: Offset.zero,
          end: const Offset(0, 0.1),
          duration: CustomAnimConfig.rapido,
          curve: CustomAnimConfig.curvaSalida,
        );
  }
}
