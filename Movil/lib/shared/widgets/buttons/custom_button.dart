import 'dart:async';
import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Botón base del cual heredarán las abstracciones de botones.
/// Controla la estructura visual, el tema, estados de carga (loading), deshabilitado,
/// soporte para iconos (prefijo/sufijo) e interacciones táctiles (ripple).
/// Si [onPressed] devuelve un Future, manejará automáticamente el estado de carga.
class CustomButton extends StatefulWidget {
  final String? text;
  final FutureOr<void> Function()? onPressed;
  final IconData? icon;
  final IconData? suffixIcon;
  final Widget? customChild;
  
  // Estados y variantes
  final bool isLoading;
  final bool isDisabled;
  final bool isSecondary;
  final bool isOutline;
  final bool isText;
  final bool isDanger;
  final bool isFullWidth;
  
  // Personalización visual
  final Color? backgroundColor;
  final Color? textColor;
  final Color? borderColor;
  final double? borderWidth;
  final double borderRadius;
  final EdgeInsetsGeometry? padding;
  final double? width;
  final double? height;
  final double elevation;
  final double iconSize;
  final double iconSpacing;
  final TextStyle? textStyle;
  final MainAxisAlignment mainAxisAlignment;

  const CustomButton({
    super.key,
    this.text,
    this.onPressed,
    this.icon,
    this.suffixIcon,
    this.customChild,
    this.isLoading = false,
    this.isDisabled = false,
    this.isSecondary = false,
    this.isOutline = false,
    this.isText = false,
    this.isDanger = false,
    this.isFullWidth = false,
    this.backgroundColor,
    this.textColor,
    this.borderColor,
    this.borderWidth,
    this.borderRadius = 12.0,
    this.padding,
    this.width,
    this.height = 48.0,
    this.elevation = 0.0,
    this.iconSize = 20.0,
    this.iconSpacing = 8.0,
    this.textStyle,
    this.mainAxisAlignment = MainAxisAlignment.center,
  });

  @override
  State<CustomButton> createState() => _CustomButtonState();
}

class _CustomButtonState extends State<CustomButton> {
  bool _isInternalLoading = false;

  void _handlePress() async {
    if (widget.onPressed == null) return;
    
    final result = widget.onPressed!();
    if (result is Future) {
      if (mounted) {
        setState(() {
          _isInternalLoading = true;
        });
      }
      try {
        await result;
      } finally {
        if (mounted) {
          setState(() {
            _isInternalLoading = false;
          });
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;
    final bool effectiveIsLoading = widget.isLoading || _isInternalLoading;
    final bool activo = !widget.isDisabled && !effectiveIsLoading && widget.onPressed != null;

    // 1. Determinar color base según la variante
    Color resolvedBg;
    Color resolvedFg;
    Color resolvedBorder;

    if (widget.isDanger) {
      if (widget.isOutline) {
        resolvedBg = Colors.transparent;
        resolvedFg = themeColores.error;
        resolvedBorder = themeColores.error;
      } else if (widget.isText) {
        resolvedBg = Colors.transparent;
        resolvedFg = themeColores.error;
        resolvedBorder = Colors.transparent;
      } else {
        resolvedBg = themeColores.error;
        resolvedFg = Colors.white;
        resolvedBorder = Colors.transparent;
      }
    } else if (widget.isSecondary) {
      if (widget.isOutline) {
        resolvedBg = Colors.transparent;
        resolvedFg = themeColores.secundario;
        resolvedBorder = themeColores.secundario;
      } else if (widget.isText) {
        resolvedBg = Colors.transparent;
        resolvedFg = themeColores.secundario;
        resolvedBorder = Colors.transparent;
      } else {
        resolvedBg = themeColores.secundario;
        resolvedFg = Colors.white;
        resolvedBorder = Colors.transparent;
      }
    } else if (widget.isOutline) {
      resolvedBg = Colors.transparent;
      resolvedFg = themeColores.primario;
      resolvedBorder = themeColores.primario;
    } else if (widget.isText) {
      resolvedBg = Colors.transparent;
      resolvedFg = themeColores.primario;
      resolvedBorder = Colors.transparent;
    } else {
      // Primario por defecto
      resolvedBg = themeColores.primario;
      resolvedFg = Colors.white;
      resolvedBorder = Colors.transparent;
    }

    // Sobrescrituras explícitas
    final Color actualBg = widget.backgroundColor ?? resolvedBg;
    final Color actualFg = widget.textColor ?? resolvedFg;
    final Color actualBorder = widget.borderColor ?? resolvedBorder;
    final double actualBorderWidth = widget.borderWidth ?? (widget.isOutline ? 1.5 : 0.0);

    // Ajuste de colores en estado deshabilitado
    final Color finalBg = activo ? actualBg : (widget.isOutline || widget.isText ? Colors.transparent : themeColores.borde);
    final Color finalFg = activo ? actualFg : themeColores.textoSecundario.withValues(alpha: 0.6);
    final Color finalBorder = activo ? actualBorder : (widget.isOutline ? themeColores.borde : Colors.transparent);

    // 2. Contenido interno del botón (Texto, Iconos o Loader)
    Widget childContent;
    if (effectiveIsLoading) {
      childContent = SizedBox(
        width: widget.iconSize,
        height: widget.iconSize,
        child: CircularProgressIndicator(
          strokeWidth: 2.2,
          valueColor: AlwaysStoppedAnimation<Color>(finalFg),
        ),
      );
    } else if (widget.customChild != null) {
      childContent = widget.customChild!;
    } else {
      final List<Widget> rowChildren = [];

      if (widget.icon != null) {
        rowChildren.add(Icon(widget.icon, size: widget.iconSize, color: finalFg));
      }

      if (widget.text != null && widget.text!.isNotEmpty) {
        if (widget.icon != null) {
          rowChildren.add(SizedBox(width: widget.iconSpacing));
        }
        rowChildren.add(
          Flexible(
            child: Text(
              widget.text!,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: (widget.textStyle ?? themeTextos.boton).copyWith(
                color: finalFg,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        );
        if (widget.suffixIcon != null) {
          rowChildren.add(SizedBox(width: widget.iconSpacing));
        }
      }

      if (widget.suffixIcon != null) {
        rowChildren.add(Icon(widget.suffixIcon, size: widget.iconSize, color: finalFg));
      }

      childContent = Row(
        mainAxisSize: widget.isFullWidth ? MainAxisSize.max : MainAxisSize.min,
        mainAxisAlignment: widget.mainAxisAlignment,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: rowChildren,
      );
    }

    // 3. Estructura y contenedor con soporte para Material Ripple
    final defaultPadding = widget.padding ??
        (widget.isText
            ? const EdgeInsets.symmetric(horizontal: 10, vertical: 8)
            : const EdgeInsets.symmetric(horizontal: 14, vertical: 12));

    final effectiveWidth = widget.isFullWidth ? double.infinity : widget.width;

    return Material(
      color: finalBg,
      elevation: activo ? widget.elevation : 0.0,
      borderRadius: BorderRadius.circular(widget.borderRadius),
      child: InkWell(
        onTap: activo ? _handlePress : null,
        borderRadius: BorderRadius.circular(widget.borderRadius),
        splashColor: finalFg.withValues(alpha: 0.12),
        highlightColor: finalFg.withValues(alpha: 0.06),
        child: Container(
          width: effectiveWidth,
          height: widget.height,
          padding: defaultPadding,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(widget.borderRadius),
            border: actualBorderWidth > 0
                ? Border.all(color: finalBorder, width: actualBorderWidth)
                : null,
          ),
          alignment: (effectiveWidth != null || widget.isFullWidth) ? Alignment.center : null,
          child: childContent,
        ),
      ),
    );
  }
}
