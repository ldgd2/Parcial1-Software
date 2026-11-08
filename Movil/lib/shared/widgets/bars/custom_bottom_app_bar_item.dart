import 'package:flutter/material.dart';

/// Elemento de Navegación para la Barra Inferior (`CustomBottomNavItem`):
/// Define el icono normal, icono activo, etiqueta de texto, badge de notificaciones
/// y callback de navegación para cada pestaña.
class CustomBottomNavItem {
  final String label;
  final IconData icon;
  final IconData? activeIcon;
  final int? badgeCount;
  final VoidCallback? onTap;
  final Color? activeColor;
  final Color? inactiveColor;

  const CustomBottomNavItem({
    required this.label,
    required this.icon,
    this.activeIcon,
    this.badgeCount,
    this.onTap,
    this.activeColor,
    this.inactiveColor,
  });
}
