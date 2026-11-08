import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_card.dart';

/// Tarjeta Informativa (`CustomInfoCard`):
/// Abstracción de alto nivel para mostrar notas, avisos, explicaciones o mensajes con icono,
/// evitando construir manualmente estructuras `Row` o `Column` en las pantallas.
class CustomInfoCard extends StatelessWidget {
  final String title;
  final String? description;
  final IconData? icon;
  final Color? iconColor;
  final Color? backgroundColor;
  final Widget? trailing;
  final VoidCallback? onTap;

  const CustomInfoCard({
    super.key,
    required this.title,
    this.description,
    this.icon,
    this.iconColor,
    this.backgroundColor,
    this.trailing,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;
    final resolvedIconColor = iconColor ?? themeColores.primario;

    return CustomCard(
      onTap: onTap,
      backgroundColor: backgroundColor,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          if (icon != null) ...[
            Icon(icon, color: resolvedIconColor, size: 26),
            const SizedBox(width: 14),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  title,
                  style: themeTextos.cuerpo.copyWith(
                    fontWeight: FontWeight.bold,
                    color: themeColores.textoPrincipal,
                  ),
                ),
                if (description != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    description!,
                    style: themeTextos.cuerpoPequeno.copyWith(
                      color: themeColores.textoSecundario,
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (trailing != null) ...[
            const SizedBox(width: 10),
            trailing!,
          ],
        ],
      ),
    );
  }
}
