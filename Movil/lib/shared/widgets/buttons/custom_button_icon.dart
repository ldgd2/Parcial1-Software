import 'package:flutter/material.dart';
import 'custom_button.dart';

/// Botón de Icono: Botón optimizado para acciones compactas con icono (circular o cuadrado).
/// Ideal para barras de navegación, botones flotantes, acciones en tarjetas y herramientas.
class CustomIconButton extends CustomButton {
  const CustomIconButton({
    super.key,
    required IconData icon,
    super.onPressed,
    super.isLoading = false,
    super.isDisabled = false,
    super.isSecondary = false,
    super.isOutline = false,
    super.isDanger = false,
    super.isText = false,
    double size = 44.0,
    super.iconSize = 22.0,
    double borderRadius = 12.0,
    bool isCircle = false,
    super.backgroundColor,
    super.textColor,
    super.borderColor,
    super.borderWidth,
    super.elevation = 0.0,
  }) : super(
          icon: icon,
          width: size,
          height: size,
          borderRadius: isCircle ? 999.0 : borderRadius,
          padding: EdgeInsets.zero,
        );
}
