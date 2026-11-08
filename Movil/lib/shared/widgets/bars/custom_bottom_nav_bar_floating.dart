import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_bottom_app_bar_item.dart';

/// Barra de Navegación Flotante (`CustomFloatingBottomBar`):
/// Barra de navegación moderna en formato cápsula/isla flotante con bordes redondeados y sombra.
class CustomFloatingBottomBar extends StatelessWidget {
  final List<CustomBottomNavItem> items;
  final int currentIndex;
  final ValueChanged<int>? onItemSelected;
  final Color? backgroundColor;
  final Color? activeColor;
  final Color? inactiveColor;
  final double borderRadius;
  final EdgeInsetsGeometry margin;
  final double elevation;

  const CustomFloatingBottomBar({
    super.key,
    required this.items,
    this.currentIndex = 0,
    this.onItemSelected,
    this.backgroundColor,
    this.activeColor,
    this.inactiveColor,
    this.borderRadius = 28.0,
    this.margin = const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
    this.elevation = 10.0,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    final resolvedBg = backgroundColor ?? themeColores.fondoSecundario;
    final resolvedActive = activeColor ?? themeColores.primario;
    final resolvedInactive = inactiveColor ?? themeColores.textoSecundario.withValues(alpha: 0.7);

    return Container(
      margin: margin,
      decoration: BoxDecoration(
        color: resolvedBg,
        borderRadius: BorderRadius.circular(borderRadius),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.12),
            blurRadius: elevation,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: List.generate(items.length, (index) {
          final item = items[index];
          final isSelected = currentIndex == index;
          final itemColor = isSelected ? resolvedActive : resolvedInactive;
          final displayIcon = isSelected ? (item.activeIcon ?? item.icon) : item.icon;

          return Expanded(
            child: InkWell(
              onTap: () {
                item.onTap?.call();
                onItemSelected?.call(index);
              },
              borderRadius: BorderRadius.circular(20),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 6.0),
                decoration: BoxDecoration(
                  color: isSelected
                      ? resolvedActive.withValues(alpha: 0.12)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Stack(
                      clipBehavior: Clip.none,
                      children: [
                        Icon(displayIcon, color: itemColor, size: 22),
                        if (item.badgeCount != null && item.badgeCount! > 0)
                          Positioned(
                            top: -2,
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
                                  fontSize: 8.5,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 3),
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
            ),
          );
        }),
      ),
    );
  }
}
