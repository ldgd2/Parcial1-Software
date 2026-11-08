import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Tarjeta Banner Promocional (`CustomBannerCard`):
/// Tarjeta visualmente atractiva con degradado (gradient), título, descripción, botón de acción e icono decorativo.
/// Perfecta para suscripciones Premium, novedades, ofertas o llamadas a la acción destacadas.
class CustomBannerCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final String? buttonText;
  final VoidCallback? onButtonPressed;
  final VoidCallback? onTap;
  final IconData? icon;
  final Gradient? gradient;
  final Color? buttonTextColor;
  final Color? buttonBackgroundColor;
  final double borderRadius;

  const CustomBannerCard({
    super.key,
    required this.title,
    required this.subtitle,
    this.buttonText,
    this.onButtonPressed,
    this.onTap,
    this.icon,
    this.gradient,
    this.buttonTextColor,
    this.buttonBackgroundColor,
    this.borderRadius = 18.0,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;

    final resolvedGradient = gradient ??
        LinearGradient(
          colors: [
            themeColores.primario,
            themeColores.secundario,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        );

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(borderRadius),
        gradient: resolvedGradient,
        boxShadow: [
          BoxShadow(
            color: themeColores.primario.withValues(alpha: 0.3),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(borderRadius),
          child: Stack(
            children: [
              // Icono decorativo translúcido de fondo
              if (icon != null)
                Positioned(
                  right: -10,
                  bottom: -15,
                  child: Icon(
                    icon,
                    size: 110,
                    color: Colors.white.withValues(alpha: 0.15),
                  ),
                ),

              // Contenido frontal
              Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      subtitle,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.88),
                        fontSize: 13,
                        height: 1.3,
                      ),
                    ),
                    if (buttonText != null) ...[
                      const SizedBox(height: 14),
                      ElevatedButton(
                        onPressed: onButtonPressed ?? onTap,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: buttonBackgroundColor ?? Colors.white,
                          foregroundColor: buttonTextColor ?? themeColores.primario,
                          elevation: 0,
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                        child: Text(
                          buttonText!,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
