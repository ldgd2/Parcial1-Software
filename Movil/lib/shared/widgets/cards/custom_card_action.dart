import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_card.dart';

/// Tarjeta de Acción y Selección (`CustomActionCard`):
/// Ideal para opciones seleccionables (Métodos de pago, Direcciones de envío, Planes de suscripción o Menús).
class CustomActionCard extends StatelessWidget {
  final String title;
  final String? subtitle;
  final IconData? icon;
  final Widget? trailing;
  final bool isSelected;
  final bool showChevron;
  final VoidCallback? onTap;
  final Color? activeColor;

  const CustomActionCard({
    super.key,
    required this.title,
    this.subtitle,
    this.icon,
    this.trailing,
    this.isSelected = false,
    this.showChevron = false,
    this.onTap,
    this.activeColor,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    final resolvedActive = activeColor ?? themeColores.primario;

    return CustomCard(
      onTap: onTap,
      borderColor: isSelected ? resolvedActive : null,
      borderWidth: isSelected ? 1.8 : 1.0,
      backgroundColor: isSelected
          ? resolvedActive.withValues(alpha: 0.05)
          : themeColores.fondoSecundario,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          // Icono en caja redondeada
          if (icon != null) ...[
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: isSelected
                    ? resolvedActive.withValues(alpha: 0.15)
                    : themeColores.borde.withValues(alpha: 0.4),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                icon,
                color: isSelected ? resolvedActive : themeColores.textoSecundario,
                size: 22,
              ),
            ),
            const SizedBox(width: 14),
          ],

          // Título y Subtítulo
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  title,
                  style: themeTextos.cuerpo.copyWith(
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.w600,
                    color: isSelected ? resolvedActive : themeColores.textoPrincipal,
                  ),
                ),
                if (subtitle != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    subtitle!,
                    style: themeTextos.cuerpoPequeno.copyWith(
                      color: themeColores.textoSecundario,
                      fontSize: 12,
                    ),
                  ),
                ],
              ],
            ),
          ),

          // Indicador de selección o Chevron
          if (trailing != null)
            trailing!
          else if (isSelected)
            Icon(
              Icons.check_circle,
              color: resolvedActive,
              size: 22,
            )
          else if (showChevron)
            Icon(
              Icons.chevron_right,
              color: themeColores.textoSecundario,
              size: 22,
            ),
        ],
      ),
    );
  }
}
