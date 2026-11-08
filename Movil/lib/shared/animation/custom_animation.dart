import 'package:flutter/material.dart';

/// Archivo principal (Base & Exporter) del Sistema Modular de Animaciones.
/// Exporta todos los módulos para que el resto de la app solo necesite importar este archivo.
export 'transitions/custom_transition.dart';
export 'warnings/custom_warning.dart';
export 'status/custom_status.dart';
export 'interactions/custom_interaction.dart';

/// Configuraciones globales de animación para mantener consistencia visual en toda la app.
class CustomAnimConfig {
  static const Duration rapido = Duration(milliseconds: 200);
  static const Duration normal = Duration(milliseconds: 400);
  static const Duration lento = Duration(milliseconds: 800);
  
  static const Curve curvaEntrada = Curves.easeOutCubic;
  static const Curve curvaSalida = Curves.easeInCubic;
  static const Curve curvaRebote = Curves.elasticOut;
  static const Curve curvaSuave = Curves.easeInOut;
}
