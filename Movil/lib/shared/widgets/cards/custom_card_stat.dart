import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_card.dart';

/// Tarjeta de Estadística / Métrica (`CustomStatCard`):
/// Diseñada para dashboards, resúmenes financieros, analíticas e indicadores clave (KPIs).
class CustomStatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color? iconColor;
  final Color? iconBackgroundColor;
  final String? trendText;
  final bool isPositiveTrend;
  final String? subtitle;
  final VoidCallback? onTap;
  final double? width;

  const CustomStatCard({
    super.key,
    required this.title,
    required this.value,
    required this.icon,
    this.iconColor,
    this.iconBackgroundColor,
    this.trendText,
    this.isPositiveTrend = true,
    this.subtitle,
    this.onTap,
    this.width,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    final resolvedIconColor = iconColor ?? themeColores.primario;
    final resolvedIconBg = iconBackgroundColor ?? resolvedIconColor.withValues(alpha: 0.12);

    return CustomCard(
      width: width,
      onTap: onTap,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Icono en caja redondeada
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: resolvedIconBg,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  icon,
                  color: resolvedIconColor,
                  size: 20,
                ),
              ),

              // Píldora de Tendencia adaptable (+14.2% o -3.1%)
              if (trendText != null)
                Flexible(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                      decoration: BoxDecoration(
                        color: (isPositiveTrend ? themeColores.exito : themeColores.error).withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            isPositiveTrend ? Icons.trending_up : Icons.trending_down,
                            size: 13,
                            color: isPositiveTrend ? themeColores.exito : themeColores.error,
                          ),
                          const SizedBox(width: 3),
                          Text(
                            trendText!,
                            style: TextStyle(
                              color: isPositiveTrend ? themeColores.exito : themeColores.error,
                              fontSize: 10.5,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),

          // Título de la métrica
          Text(
            title,
            style: themeTextos.cuerpoPequeno.copyWith(
              color: themeColores.textoSecundario,
              fontWeight: FontWeight.w500,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),

          // Valor numérico destacado
          Text(
            value,
            style: themeTextos.titulo.copyWith(
              fontWeight: FontWeight.bold,
              letterSpacing: -0.5,
            ),
          ),

          // Subtítulo comparativo opcional (ej. "vs. mes anterior")
          if (subtitle != null) ...[
            const SizedBox(height: 4),
            Text(
              subtitle!,
              style: themeTextos.cuerpoPequeno.copyWith(
                fontSize: 11,
                color: themeColores.textoSecundario.withValues(alpha: 0.8),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
