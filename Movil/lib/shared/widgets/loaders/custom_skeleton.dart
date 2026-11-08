import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import '../../animation/custom_animation.dart';

/// Bloque gris brillante (Skeleton) para simular contenido que está cargando.
/// Funciona perfectamente integrado con el sistema de animaciones mediante `animarCarga()`.
class CustomSkeleton extends StatelessWidget {
  final double? width;
  final double? height;
  final double borderRadius;
  final bool isCircle;
  final EdgeInsetsGeometry? margin;

  const CustomSkeleton({
    super.key,
    this.width,
    this.height,
    this.borderRadius = 8.0,
    this.isCircle = false,
    this.margin,
  });

  /// Esqueleto típico para una línea de texto corto
  factory CustomSkeleton.text({double width = 120, double height = 14, EdgeInsetsGeometry? margin}) {
    return CustomSkeleton(width: width, height: height, borderRadius: 4, margin: margin);
  }
  
  /// Esqueleto típico para títulos o encabezados (más grueso)
  factory CustomSkeleton.heading({double width = 200, double height = 20, EdgeInsetsGeometry? margin}) {
    return CustomSkeleton(width: width, height: height, borderRadius: 6, margin: margin);
  }

  /// Esqueleto para avatares, fotos de perfil o iconos
  factory CustomSkeleton.circle({double size = 48, EdgeInsetsGeometry? margin}) {
    return CustomSkeleton(width: size, height: size, isCircle: true, margin: margin);
  }

  /// Esqueleto para imágenes de artículos, banners o portadas
  factory CustomSkeleton.image({double width = double.infinity, double height = 150, EdgeInsetsGeometry? margin}) {
    return CustomSkeleton(width: width, height: height, borderRadius: 12, margin: margin);
  }

  // =========================================================================
  // ESTRUCTURAS COMPUESTAS (Skeletons Abstractos pre-armados)
  // =========================================================================

  /// Esqueleto que simula un párrafo de texto de varias líneas.
  static Widget paragraph({int lines = 3, double spacing = 8.0, EdgeInsetsGeometry? margin}) {
    return Padding(
      padding: margin ?? EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: List.generate(lines, (index) {
          // La última línea la hacemos más corta para simular texto real
          final isLast = index == lines - 1;
          return CustomSkeleton.text(
            width: isLast ? 150 : double.infinity, 
            height: 14, 
            margin: EdgeInsets.only(bottom: isLast ? 0 : spacing)
          );
        }),
      ),
    );
  }

  /// Esqueleto que simula un elemento de lista (Avatar + Título + Subtítulo).
  static Widget listTile({bool hasSubtitle = true, bool hasLeading = true, EdgeInsetsGeometry? margin}) {
    return Padding(
      padding: margin ?? EdgeInsets.zero,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          if (hasLeading) ...[
            CustomSkeleton.circle(size: 48),
            const SizedBox(width: 16),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                CustomSkeleton.heading(width: 140),
                if (hasSubtitle) ...[
                  const SizedBox(height: 8),
                  CustomSkeleton.text(width: double.infinity),
                ]
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Esqueleto que simula una tarjeta (Card) completa (Imagen + Texto + Botones).
  static Widget card({double imageHeight = 150, EdgeInsetsGeometry? margin}) {
    return Container(
      margin: margin,
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05), // Fondo ultra tenue para contener la tarjeta
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CustomSkeleton.image(height: imageHeight),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CustomSkeleton.heading(width: 180),
                const SizedBox(height: 8),
                CustomSkeleton.paragraph(lines: 2),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    CustomSkeleton.circle(size: 32),
                    CustomSkeleton(width: 80, height: 32, borderRadius: 20), // Botón
                  ],
                )
              ],
            ),
          )
        ],
      ),
    );
  }
  
  /// Esqueleto para simular el perfil de un usuario (Header con avatar centrado).
  static Widget profile({EdgeInsetsGeometry? margin}) {
    return Padding(
      padding: margin ?? EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          CustomSkeleton.circle(size: 100),
          const SizedBox(height: 16),
          CustomSkeleton.heading(width: 160),
          const SizedBox(height: 8),
          CustomSkeleton.text(width: 100),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              CustomSkeleton.heading(width: 60, height: 40),
              CustomSkeleton.heading(width: 60, height: 40),
              CustomSkeleton.heading(width: 60, height: 40),
            ],
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    
    // Usamos el color de borde como base (es un gris neutro que contrasta bien)
    final baseColor = themeColores.borde;
    
    Widget skeletonBlock = Container(
      width: width,
      height: height,
      margin: margin,
      decoration: BoxDecoration(
        color: baseColor,
        shape: isCircle ? BoxShape.circle : BoxShape.rectangle,
        borderRadius: isCircle ? null : BorderRadius.circular(borderRadius),
      ),
    );

    // Le aplicamos el Shimmer de nuestro propio sistema modular
    return skeletonBlock.animarCarga(
      isLoading: true,
      shimmerColor: themeColores.fondoSecundario.withValues(alpha: 0.5),
    );
  }
}
