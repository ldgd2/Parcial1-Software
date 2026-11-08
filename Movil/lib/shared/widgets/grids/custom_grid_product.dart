import 'package:flutter/material.dart';
import '../cards/custom_card_product.dart';
import 'custom_grid.dart';

/// Cuadrícula de Productos E-Commerce (`CustomProductGrid`):
/// Organiza tarjetas de catálogo de productos en 2 columnas con aspect ratio optimizado
/// para evitar desbordamientos y permitir scroll fluido.
class CustomProductGrid extends StatelessWidget {
  final List<CustomProductCard> products;
  final int crossAxisCount;
  final double spacing;
  final double childAspectRatio;

  const CustomProductGrid({
    super.key,
    required this.products,
    this.crossAxisCount = 2,
    this.spacing = 10.0,
    this.childAspectRatio = 0.65,
  });

  @override
  Widget build(BuildContext context) {
    return CustomGrid.count(
      crossAxisCount: crossAxisCount,
      spacing: spacing,
      childAspectRatio: childAspectRatio,
      children: products,
    );
  }
}
