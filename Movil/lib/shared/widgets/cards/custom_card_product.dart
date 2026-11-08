import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_card.dart';

/// Tarjeta de Producto (`CustomProductCard`):
/// Diseñada para catálogos y tiendas virtuales (E-Commerce).
/// Incluye área de imagen con badge de descuento/nuevo, favoritos, calificación, precio y botón de compra.
class CustomProductCard extends StatelessWidget {
  final String title;
  final String price;
  final String? originalPrice;
  final String? category;
  final Widget? imageWidget;
  final IconData placeholderIcon;
  final double? rating;
  final int? reviewsCount;
  final String? badgeText;
  final Color? badgeColor;
  final bool isFavorite;
  final VoidCallback? onFavoritePressed;
  final VoidCallback? onAddToCart;
  final VoidCallback? onTap;
  final double width;

  const CustomProductCard({
    super.key,
    required this.title,
    required this.price,
    this.originalPrice,
    this.category,
    this.imageWidget,
    this.placeholderIcon = Icons.shopping_bag_outlined,
    this.rating,
    this.reviewsCount,
    this.badgeText,
    this.badgeColor,
    this.isFavorite = false,
    this.onFavoritePressed,
    this.onAddToCart,
    this.onTap,
    this.width = 180.0,
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
          // Área Superior: Imagen + Badge + Favorito
          Stack(
            children: [
              Container(
                height: 140,
                width: double.infinity,
                color: themeColores.borde.withValues(alpha: 0.3),
                child: imageWidget ??
                    Center(
                      child: Icon(
                        placeholderIcon,
                        size: 48,
                        color: themeColores.textoSecundario.withValues(alpha: 0.5),
                      ),
                    ),
              ),

              // Badge superior izquierdo (ej. "20% OFF", "Nuevo")
              if (badgeText != null)
                Positioned(
                  top: 10,
                  left: 10,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: badgeColor ?? themeColores.primario,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      badgeText!,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),

              // Botón de Favorito superior derecho
              if (onFavoritePressed != null)
                Positioned(
                  top: 8,
                  right: 8,
                  child: Material(
                    color: Colors.white.withValues(alpha: 0.9),
                    shape: const CircleBorder(),
                    child: InkWell(
                      customBorder: const CircleBorder(),
                      onTap: onFavoritePressed,
                      child: Padding(
                        padding: const EdgeInsets.all(6),
                        child: Icon(
                          isFavorite ? Icons.favorite : Icons.favorite_border,
                          size: 18,
                          color: isFavorite ? Colors.redAccent : themeColores.textoSecundario,
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),

          // Área Inferior: Información del producto
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (category != null) ...[
                  Text(
                    category!.toUpperCase(),
                    style: themeTextos.cuerpoPequeno.copyWith(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: themeColores.textoSecundario,
                      letterSpacing: 0.5,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 3),
                ],

                Text(
                  title,
                  style: themeTextos.cuerpo.copyWith(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 6),

                // Calificación (Rating)
                if (rating != null) ...[
                  Row(
                    children: [
                      const Icon(Icons.star, size: 14, color: Color(0xFFF59E0B)),
                      const SizedBox(width: 4),
                      Text(
                        rating!.toStringAsFixed(1),
                        style: themeTextos.cuerpoPequeno.copyWith(
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                          color: themeColores.textoPrincipal,
                        ),
                      ),
                      if (reviewsCount != null) ...[
                        const SizedBox(width: 3),
                        Text(
                          "($reviewsCount)",
                          style: themeTextos.cuerpoPequeno.copyWith(
                            fontSize: 11,
                            color: themeColores.textoSecundario,
                          ),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 6),
                ],

                // Precios y Botón de añadir al carrito
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          price,
                          style: themeTextos.cuerpo.copyWith(
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                            color: themeColores.primario,
                          ),
                        ),
                        if (originalPrice != null)
                          Text(
                            originalPrice!,
                            style: themeTextos.cuerpoPequeno.copyWith(
                              fontSize: 11,
                              decoration: TextDecoration.lineThrough,
                              color: themeColores.textoSecundario,
                            ),
                          ),
                      ],
                    ),

                    if (onAddToCart != null)
                      Material(
                        color: themeColores.primario,
                        borderRadius: BorderRadius.circular(8),
                        child: InkWell(
                          borderRadius: BorderRadius.circular(8),
                          onTap: onAddToCart,
                          child: const Padding(
                            padding: EdgeInsets.all(8),
                            child: Icon(
                              Icons.add_shopping_cart,
                              size: 16,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
