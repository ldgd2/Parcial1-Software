import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_grid.dart';

/// Elemento multimedia para cuadrícula (`CustomMediaItem`)
class CustomMediaItem {
  final String? imageUrl;
  final String? title;
  final bool isVideo;
  final String? videoDuration;
  final bool isSelected;
  final VoidCallback? onTap;

  const CustomMediaItem({
    this.imageUrl,
    this.title,
    this.isVideo = false,
    this.videoDuration,
    this.isSelected = false,
    this.onTap,
  });
}

/// Cuadrícula Multimedia / Galería de Fotos y Videos (`CustomMediaGrid`):
/// Diseñada para galerías de fotos estilo teléfono, miniaturas de video, álbumes o selección de archivos.
/// Soporta overlay de "+N fotos más", indicador de video (Play) y selección múltiple.
class CustomMediaGrid extends StatelessWidget {
  final List<CustomMediaItem> items;
  final int crossAxisCount;
  final double spacing;
  final double borderRadius;
  final double childAspectRatio;
  final int? maxVisibleItems;
  final ValueChanged<int>? onMediaTap;
  final VoidCallback? onMoreTap;

  const CustomMediaGrid({
    super.key,
    required this.items,
    this.crossAxisCount = 3,
    this.spacing = 6.0,
    this.borderRadius = 12.0,
    this.childAspectRatio = 1.0,
    this.maxVisibleItems,
    this.onMediaTap,
    this.onMoreTap,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final total = items.length;
    final visibleCount = (maxVisibleItems != null && total > maxVisibleItems!)
        ? maxVisibleItems!
        : total;
    final extraCount = total - visibleCount;

    return CustomGrid.count(
      crossAxisCount: crossAxisCount,
      spacing: spacing,
      childAspectRatio: childAspectRatio,
      children: List.generate(visibleCount, (index) {
        final item = items[index];
        final isLastWithMore = index == visibleCount - 1 && extraCount > 0;

        return ClipRRect(
          borderRadius: BorderRadius.circular(borderRadius),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: isLastWithMore
                  ? onMoreTap ?? item.onTap ?? () => onMediaTap?.call(index)
                  : item.onTap ?? () => onMediaTap?.call(index),
              child: Stack(
                fit: StackFit.expand,
                children: [
                  // Imagen de fondo o placeholder estilizado
                  item.imageUrl != null && item.imageUrl!.isNotEmpty
                      ? Image.network(
                          item.imageUrl!,
                          fit: BoxFit.cover,
                          errorBuilder: (_, _, _) => _buildPlaceholder(context, index, item),
                        )
                      : _buildPlaceholder(context, index, item),

                  // Overlay para videos (Icono de Play y Duración)
                  if (item.isVideo && !isLastWithMore) ...[
                    Positioned.fill(
                      child: Container(
                        color: Colors.black.withValues(alpha: 0.2),
                        child: Center(
                          child: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: Colors.black.withValues(alpha: 0.55),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 22),
                          ),
                        ),
                      ),
                    ),
                    if (item.videoDuration != null)
                      Positioned(
                        bottom: 6,
                        right: 6,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.black.withValues(alpha: 0.65),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            item.videoDuration!,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                  ],

                  // Checkmark de selección activa
                  if (item.isSelected && !isLastWithMore)
                    Positioned(
                      top: 6,
                      right: 6,
                      child: Container(
                        padding: const EdgeInsets.all(3),
                        decoration: BoxDecoration(
                          color: themeColores.primario,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.check, color: Colors.white, size: 14),
                      ),
                    ),

                  // Overlay "+N Más"
                  if (isLastWithMore)
                    Positioned.fill(
                      child: Container(
                        color: Colors.black.withValues(alpha: 0.65),
                        child: Center(
                          child: Text(
                            "+$extraCount",
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildPlaceholder(BuildContext context, int index, CustomMediaItem item) {
    final themeColores = context.colores;
    return Container(
      decoration: BoxDecoration(
        color: themeColores.fondoSecundario,
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            themeColores.fondoSecundario,
            themeColores.primario.withValues(alpha: 0.15 + ((index % 4) * 0.05)),
          ],
        ),
      ),
      child: Center(
        child: Icon(
          item.isVideo ? Icons.videocam_outlined : Icons.photo_outlined,
          color: themeColores.textoSecundario.withValues(alpha: 0.6),
          size: 28,
        ),
      ),
    );
  }
}
