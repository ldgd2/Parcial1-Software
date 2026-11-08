import 'package:flutter/material.dart';

/// Cuadrícula Base (`CustomGrid`):
/// Proporciona una estructura de cuadrícula altamente configurable y responsiva.
/// Permite definir número de columnas fijo o adaptativo por ancho máximo (ideal para tablets/web),
/// control de scroll, espaciados y aspect ratio sin escribir delegates manuales en las pantallas.
class CustomGrid extends StatelessWidget {
  final List<Widget> children;
  final int? crossAxisCount;
  final double? maxCrossAxisExtent;
  final double crossAxisSpacing;
  final double mainAxisSpacing;
  final double childAspectRatio;
  final EdgeInsetsGeometry padding;
  final bool shrinkWrap;
  final ScrollPhysics? physics;
  final ScrollController? controller;

  const CustomGrid({
    super.key,
    required this.children,
    this.crossAxisCount = 2,
    this.maxCrossAxisExtent,
    this.crossAxisSpacing = 12.0,
    this.mainAxisSpacing = 12.0,
    this.childAspectRatio = 1.0,
    this.padding = EdgeInsets.zero,
    this.shrinkWrap = true,
    this.physics = const NeverScrollableScrollPhysics(),
    this.controller,
  });

  /// Cuadrícula con número de columnas fijo (por defecto 2 columnas)
  factory CustomGrid.count({
    required List<Widget> children,
    int crossAxisCount = 2,
    double spacing = 12.0,
    double childAspectRatio = 1.0,
    EdgeInsetsGeometry padding = EdgeInsets.zero,
    bool shrinkWrap = true,
    ScrollPhysics? physics = const NeverScrollableScrollPhysics(),
  }) {
    return CustomGrid(
      crossAxisCount: crossAxisCount,
      crossAxisSpacing: spacing,
      mainAxisSpacing: spacing,
      childAspectRatio: childAspectRatio,
      padding: padding,
      shrinkWrap: shrinkWrap,
      physics: physics,
      children: children,
    );
  }

  /// Cuadrícula adaptativa / responsiva según el ancho disponible (útil para móviles y tablets)
  factory CustomGrid.extent({
    required List<Widget> children,
    double maxCrossAxisExtent = 180.0,
    double spacing = 12.0,
    double childAspectRatio = 1.0,
    EdgeInsetsGeometry padding = EdgeInsets.zero,
    bool shrinkWrap = true,
    ScrollPhysics? physics = const NeverScrollableScrollPhysics(),
  }) {
    return CustomGrid(
      maxCrossAxisExtent: maxCrossAxisExtent,
      crossAxisSpacing: spacing,
      mainAxisSpacing: spacing,
      childAspectRatio: childAspectRatio,
      padding: padding,
      shrinkWrap: shrinkWrap,
      physics: physics,
      children: children,
    );
  }

  @override
  Widget build(BuildContext context) {
    if (maxCrossAxisExtent != null) {
      return GridView.builder(
        controller: controller,
        padding: padding,
        shrinkWrap: shrinkWrap,
        physics: physics,
        gridDelegate: SliverGridDelegateWithMaxCrossAxisExtent(
          maxCrossAxisExtent: maxCrossAxisExtent!,
          crossAxisSpacing: crossAxisSpacing,
          mainAxisSpacing: mainAxisSpacing,
          childAspectRatio: childAspectRatio,
        ),
        itemCount: children.length,
        itemBuilder: (context, index) => children[index],
      );
    }

    return GridView.builder(
      controller: controller,
      padding: padding,
      shrinkWrap: shrinkWrap,
      physics: physics,
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: crossAxisCount ?? 2,
        crossAxisSpacing: crossAxisSpacing,
        mainAxisSpacing: mainAxisSpacing,
        childAspectRatio: childAspectRatio,
      ),
      itemCount: children.length,
      itemBuilder: (context, index) => children[index],
    );
  }
}
