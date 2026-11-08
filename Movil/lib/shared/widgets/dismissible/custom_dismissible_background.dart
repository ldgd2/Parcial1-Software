import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Fondo estilizado para acciones de deslizamiento (`CustomDismissibleBackground`):
/// Proporciona fondos visuales con iconos, etiquetas y colores temáticos (Gmail / iOS / Decisiones).
class CustomDismissibleBackground extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color backgroundColor;
  final Color foregroundColor;
  final Alignment alignment;
  final double borderRadius;
  final EdgeInsetsGeometry padding;

  const CustomDismissibleBackground({
    super.key,
    required this.label,
    required this.icon,
    required this.backgroundColor,
    this.foregroundColor = Colors.white,
    this.alignment = Alignment.centerRight,
    this.borderRadius = 16.0,
    this.padding = const EdgeInsets.symmetric(horizontal: 20.0),
  });

  /// Fondo preconfigurado para Aceptar / Aprobar (Verde a la Derecha)
  factory CustomDismissibleBackground.accept({
    String label = "Aceptar",
    IconData icon = Icons.check_circle_outline_rounded,
    Color? backgroundColor,
    double borderRadius = 16.0,
  }) {
    return CustomDismissibleBackground(
      label: label,
      icon: icon,
      backgroundColor: backgroundColor ?? const Color(0xFF10B981),
      alignment: Alignment.centerLeft,
      borderRadius: borderRadius,
    );
  }

  /// Fondo preconfigurado para Rechazar / Descartar (Rojo a la Izquierda)
  factory CustomDismissibleBackground.reject({
    String label = "Rechazar",
    IconData icon = Icons.close_rounded,
    Color? backgroundColor,
    double borderRadius = 16.0,
  }) {
    return CustomDismissibleBackground(
      label: label,
      icon: icon,
      backgroundColor: backgroundColor ?? const Color(0xFFEF4444),
      alignment: Alignment.centerRight,
      borderRadius: borderRadius,
    );
  }

  /// Fondo preconfigurado para Eliminar / Borrar (Rojo con icono de papelera)
  factory CustomDismissibleBackground.delete({
    String label = "Eliminar",
    IconData icon = Icons.delete_outline_rounded,
    Color? backgroundColor,
    double borderRadius = 16.0,
  }) {
    return CustomDismissibleBackground(
      label: label,
      icon: icon,
      backgroundColor: backgroundColor ?? const Color(0xFFEF4444),
      alignment: Alignment.centerRight,
      borderRadius: borderRadius,
    );
  }

  /// Fondo preconfigurado para Archivar (Azul con icono de archivo)
  factory CustomDismissibleBackground.archive({
    String label = "Archivar",
    IconData icon = Icons.archive_outlined,
    Color? backgroundColor,
    double borderRadius = 16.0,
  }) {
    return CustomDismissibleBackground(
      label: label,
      icon: icon,
      backgroundColor: backgroundColor ?? const Color(0xFF3B82F6),
      alignment: Alignment.centerLeft,
      borderRadius: borderRadius,
    );
  }

  /// Fondo preconfigurado para Marcar como Completado / Hecho (Verde)
  factory CustomDismissibleBackground.complete({
    String label = "Completar",
    IconData icon = Icons.check_circle_outline_rounded,
    Color? backgroundColor,
    double borderRadius = 16.0,
  }) {
    return CustomDismissibleBackground(
      label: label,
      icon: icon,
      backgroundColor: backgroundColor ?? const Color(0xFF10B981),
      alignment: Alignment.centerLeft,
      borderRadius: borderRadius,
    );
  }

  /// Fondo preconfigurado para Marcar como Favorito / Destacar (Ámbar/Amarillo)
  factory CustomDismissibleBackground.favorite({
    String label = "Favorito",
    IconData icon = Icons.star_border_rounded,
    Color? backgroundColor,
    double borderRadius = 16.0,
  }) {
    return CustomDismissibleBackground(
      label: label,
      icon: icon,
      backgroundColor: backgroundColor ?? const Color(0xFFF59E0B),
      alignment: Alignment.centerLeft,
      borderRadius: borderRadius,
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeTextos = context.textos;
    final isLeftAligned = alignment == Alignment.centerLeft || alignment == Alignment.topLeft;

    return Container(
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(borderRadius),
      ),
      padding: padding,
      alignment: alignment,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (isLeftAligned) ...[
            Icon(icon, color: foregroundColor, size: 24),
            const SizedBox(width: 8),
            Text(
              label,
              style: themeTextos.cuerpoPequeno.copyWith(
                color: foregroundColor,
                fontWeight: FontWeight.bold,
              ),
            ),
          ] else ...[
            Text(
              label,
              style: themeTextos.cuerpoPequeno.copyWith(
                color: foregroundColor,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(width: 8),
            Icon(icon, color: foregroundColor, size: 24),
          ],
        ],
      ),
    );
  }
}
