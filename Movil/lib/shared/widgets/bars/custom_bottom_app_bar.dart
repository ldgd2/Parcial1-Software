import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_bottom_app_bar_item.dart';

/// Barra Inferior de Navegación con Hueco/Mordida para FAB (`CustomBottomAppBar`):
/// Proporciona un `BottomAppBar` con muesca curva (`CircularNotchedRectangle`)
/// donde encaja de forma elegante el Botón Flotante (`FloatingActionButtonLocation.centerDocked`).
/// Distribuye simétricamente los elementos a los lados del botón central.
class CustomBottomAppBar extends StatelessWidget {
  final List<CustomBottomNavItem> items;
  final int currentIndex;
  final ValueChanged<int>? onItemSelected;
  final Color? backgroundColor;
  final Color? activeColor;
  final Color? inactiveColor;
  final double elevation;
  final double height;
  final double notchMargin;
  final double iconSize;

  const CustomBottomAppBar({
    super.key,
    required this.items,
    this.currentIndex = 0,
    this.onItemSelected,
    this.backgroundColor,
    this.activeColor,
    this.inactiveColor,
    this.elevation = 8.0,
    this.height = 64.0,
    this.notchMargin = 8.0,
    this.iconSize = 24.0,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    final resolvedBg = backgroundColor ?? themeColores.fondoSecundario;
    final resolvedActive = activeColor ?? themeColores.primario;
    final resolvedInactive = inactiveColor ?? themeColores.textoSecundario.withValues(alpha: 0.7);

    // Dividir items en dos mitades (Izquierda y Derecha del Notch central)
    final int total = items.length;
    final int middleIndex = (total / 2).ceil();

    final List<CustomBottomNavItem> leftItems = items.sublist(0, middleIndex);
    final List<CustomBottomNavItem> rightItems = items.sublist(middleIndex);

    return BottomAppBar(
      color: resolvedBg,
      elevation: elevation,
      height: height,
      padding: EdgeInsets.zero,
      shape: const CircularNotchedRectangle(),
      notchMargin: notchMargin,
      clipBehavior: Clip.antiAlias,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          // 1. Grupo Izquierdo de Ítems
          Expanded(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: List.generate(leftItems.length, (i) {
                return _buildNavItem(
                  context: context,
                  item: leftItems[i],
                  index: i,
                  isSelected: currentIndex == i,
                  activeColor: resolvedActive,
                  inactiveColor: resolvedInactive,
                  themeTextos: themeTextos,
                  themeColores: themeColores,
                );
              }),
            ),
          ),

          // 2. Espacio central reservado para el Notch / FAB
          const SizedBox(width: 48),

          // 3. Grupo Derecho de Ítems
          Expanded(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: List.generate(rightItems.length, (i) {
                final realIndex = middleIndex + i;
                return _buildNavItem(
                  context: context,
                  item: rightItems[i],
                  index: realIndex,
                  isSelected: currentIndex == realIndex,
                  activeColor: resolvedActive,
                  inactiveColor: resolvedInactive,
                  themeTextos: themeTextos,
                  themeColores: themeColores,
                );
              }),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem({
    required BuildContext context,
    required CustomBottomNavItem item,
    required int index,
    required bool isSelected,
    required Color activeColor,
    required Color inactiveColor,
    required AppTextos themeTextos,
    required AppColores themeColores,
  }) {
    final itemColor = isSelected
        ? (item.activeColor ?? activeColor)
        : (item.inactiveColor ?? inactiveColor);

    final displayIcon = isSelected ? (item.activeIcon ?? item.icon) : item.icon;

    return Expanded(
      child: InkWell(
        onTap: () {
          item.onTap?.call();
          onItemSelected?.call(index);
        },
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            // Icono con Badge
            Stack(
              clipBehavior: Clip.none,
              children: [
                Icon(
                  displayIcon,
                  color: itemColor,
                  size: iconSize,
                ),
                if (item.badgeCount != null && item.badgeCount! > 0)
                  Positioned(
                    top: -3,
                    right: -6,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                      decoration: BoxDecoration(
                        color: themeColores.error,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        item.badgeCount! > 99 ? "99+" : "${item.badgeCount}",
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 3),

            // Etiqueta de texto
            Text(
              item.label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: themeTextos.cuerpoPequeno.copyWith(
                fontSize: 10.5,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                color: itemColor,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
