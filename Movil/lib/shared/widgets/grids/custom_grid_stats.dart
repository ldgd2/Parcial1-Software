import 'package:flutter/material.dart';
import '../cards/custom_card_stat.dart';
import 'custom_grid.dart';

/// Cuadrícula de Métricas y Estadísticas (`CustomStatsGrid`):
/// Organiza tarjetas de indicadores clave (KPIs), analíticas y métricas financieras
/// en una cuadrícula responsiva optimizada para paneles de control (Dashboards).
class CustomStatsGrid extends StatelessWidget {
  final List<CustomStatCard> stats;
  final int crossAxisCount;
  final double spacing;
  final double childAspectRatio;

  const CustomStatsGrid({
    super.key,
    required this.stats,
    this.crossAxisCount = 2,
    this.spacing = 12.0,
    this.childAspectRatio = 1.35,
  });

  @override
  Widget build(BuildContext context) {
    return CustomGrid.count(
      crossAxisCount: crossAxisCount,
      spacing: spacing,
      childAspectRatio: childAspectRatio,
      children: stats,
    );
  }
}
