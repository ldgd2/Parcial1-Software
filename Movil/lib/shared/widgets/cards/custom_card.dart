import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Tarjeta Base (`CustomCard`):
/// El bloque visual fundamental con esquinas redondeadas, sombra suave y respuesta táctil.
/// Base centralizada para todas las variantes especializadas de tarjetas de la aplicación.
class CustomCard extends StatelessWidget {
  final Widget? child;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry padding;
  final EdgeInsetsGeometry? margin;
  final Color? backgroundColor;
  final Color? borderColor;
  final double borderWidth;
  final double borderRadius;
  final double elevation;
  final bool hasShadow;
  final double? width;
  final double? height;
  final Clip clipBehavior;

  const CustomCard({
    super.key,
    this.child,
    this.onTap,
    this.padding = const EdgeInsets.all(16.0),
    this.margin,
    this.backgroundColor,
    this.borderColor,
    this.borderWidth = 1.0,
    this.borderRadius = 16.0,
    this.elevation = 0.0,
    this.hasShadow = true,
    this.width,
    this.height,
    this.clipBehavior = Clip.antiAlias,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final cardBg = backgroundColor ?? themeColores.fondoSecundario;
    final resolvedBorderColor = borderColor ?? themeColores.borde.withValues(alpha: 0.6);

    Widget cardWidget = Container(
      width: width,
      height: height,
      margin: margin,
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(borderRadius),
        border: borderWidth > 0
            ? Border.all(color: resolvedBorderColor, width: borderWidth)
            : null,
        boxShadow: hasShadow
            ? [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.04),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ]
            : null,
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(borderRadius),
        clipBehavior: clipBehavior,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(borderRadius),
          splashColor: themeColores.primario.withValues(alpha: 0.08),
          highlightColor: themeColores.primario.withValues(alpha: 0.04),
          child: Padding(
            padding: padding,
            child: child,
          ),
        ),
      ),
    );

    return cardWidget;
  }
}
