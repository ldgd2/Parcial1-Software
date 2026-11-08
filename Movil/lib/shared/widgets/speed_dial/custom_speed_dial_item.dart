import 'package:flutter/material.dart';

/// Elemento de Acción para Speed Dial (`CustomSpeedDialItem`):
/// Define el icono, etiqueta, colores y comportamiento de cada botón secundario
/// que se despliega al abrir el menú flotante.
class CustomSpeedDialItem {
  final String label;
  final IconData icon;
  final VoidCallback onPressed;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final Color? labelBackgroundColor;
  final Color? labelTextColor;
  final double iconSize;

  const CustomSpeedDialItem({
    required this.label,
    required this.icon,
    required this.onPressed,
    this.backgroundColor,
    this.foregroundColor,
    this.labelBackgroundColor,
    this.labelTextColor,
    this.iconSize = 22.0,
  });
}
