import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_grid.dart';

/// Elemento de acción para la matriz de accesos rápidos (`CustomMatrixItem`)
class CustomMatrixItem {
  final String label;
  final IconData icon;
  final Color? color;
  final Color? iconBackgroundColor;
  final int? badgeCount;
  final bool isFeatured;
  final VoidCallback? onTap;

  const CustomMatrixItem({
    required this.label,
    required this.icon,
    this.color,
    this.iconBackgroundColor,
    this.badgeCount,
    this.isFeatured = false,
    this.onTap,
  });
}

/// Matriz de Accesos Rápidos y Menús (`CustomMatrixGrid`):
/// Ideal para paneles de inicio (ej. apps bancarias, centros de servicios o launchers de apps).
/// Organiza iconos en badges redondeados con títulos y badges numéricos de notificación.
class CustomMatrixGrid extends StatelessWidget {
  final List<CustomMatrixItem> items;
  final int crossAxisCount;
  final double spacing;
  final double iconSize;
  final double badgeSize;
  final double borderRadius;
  final Color? tileBackgroundColor;

  const CustomMatrixGrid({
    super.key,
    required this.items,
    this.crossAxisCount = 4,
    this.spacing = 10.0,
    this.iconSize = 24.0,
    this.badgeSize = 52.0,
    this.borderRadius = 16.0,
    this.tileBackgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    return CustomGrid.count(
      crossAxisCount: crossAxisCount,
      spacing: spacing,
      childAspectRatio: 0.88,
      children: items.map((item) {
        final itemColor = item.color ?? themeColores.primario;
        final iconBg = item.iconBackgroundColor ?? itemColor.withValues(alpha: 0.12);

        return Material(
          color: tileBackgroundColor ?? Colors.transparent,
          borderRadius: BorderRadius.circular(borderRadius),
          child: InkWell(
            onTap: item.onTap,
            borderRadius: BorderRadius.circular(borderRadius),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 4.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // Badge circular con el icono y badge de notificación
                  Stack(
                    clipBehavior: Clip.none,
                    children: [
                      Container(
                        width: badgeSize,
                        height: badgeSize,
                        decoration: BoxDecoration(
                          color: iconBg,
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Icon(
                            item.icon,
                            color: itemColor,
                            size: iconSize,
                          ),
                        ),
                      ),

                      // Contador de notificación (ej. "3")
                      if (item.badgeCount != null && item.badgeCount! > 0)
                        Positioned(
                          top: -2,
                          right: -2,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                            decoration: BoxDecoration(
                              color: themeColores.error,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: themeColores.fondo, width: 1.5),
                            ),
                            child: Text(
                              item.badgeCount! > 99 ? "99+" : "${item.badgeCount}",
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 9.5,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  // Etiqueta de la acción
                  Text(
                    item.label,
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: themeTextos.cuerpoPequeno.copyWith(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w600,
                      color: themeColores.textoPrincipal,
                      height: 1.15,
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
