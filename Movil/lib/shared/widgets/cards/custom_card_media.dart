import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_card.dart';

/// Tarjeta de Contenido / Artículo (`CustomMediaCard`):
/// Ideal para blogs, noticias, tutoriales, videos o publicaciones informativas.
class CustomMediaCard extends StatelessWidget {
  final String title;
  final String? snippet;
  final String? category;
  final String? date;
  final String? readTime;
  final Widget? imageWidget;
  final IconData placeholderIcon;
  final bool isBookmarked;
  final VoidCallback? onBookmark;
  final VoidCallback? onTap;
  final double? width;

  const CustomMediaCard({
    super.key,
    required this.title,
    this.snippet,
    this.category,
    this.date,
    this.readTime,
    this.imageWidget,
    this.placeholderIcon = Icons.article_outlined,
    this.isBookmarked = false,
    this.onBookmark,
    this.onTap,
    this.width,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    return CustomCard(
      width: width,
      padding: EdgeInsets.zero,
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Imagen de portada
          Container(
            height: 140,
            width: double.infinity,
            color: themeColores.borde.withValues(alpha: 0.3),
            child: imageWidget ??
                Center(
                  child: Icon(
                    placeholderIcon,
                    size: 40,
                    color: themeColores.textoSecundario.withValues(alpha: 0.5),
                  ),
                ),
          ),

          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Categoría y tiempo de lectura
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    if (category != null)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: themeColores.primario.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          category!,
                          style: TextStyle(
                            color: themeColores.primario,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    if (readTime != null || date != null)
                      Text(
                        date != null && readTime != null
                            ? "$date • $readTime"
                            : (date ?? readTime!),
                        style: themeTextos.cuerpoPequeno.copyWith(
                          fontSize: 11,
                          color: themeColores.textoSecundario,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 8),

                // Título
                Text(
                  title,
                  style: themeTextos.cuerpo.copyWith(
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),

                // Resumen
                if (snippet != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    snippet!,
                    style: themeTextos.cuerpoPequeno.copyWith(
                      color: themeColores.textoSecundario,
                      fontSize: 12,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],

                // Botón de guardar / bookmark
                if (onBookmark != null) ...[
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerRight,
                    child: GestureDetector(
                      onTap: onBookmark,
                      child: Icon(
                        isBookmarked ? Icons.bookmark : Icons.bookmark_border,
                        size: 20,
                        color: isBookmarked ? themeColores.primario : themeColores.textoSecundario,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
