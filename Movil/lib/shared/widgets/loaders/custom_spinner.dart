import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Indicador de carga circular clásico (Spinner).
class CustomSpinner extends StatelessWidget {
  final double size;
  final Color? color;
  final double strokeWidth;

  const CustomSpinner({
    super.key,
    this.size = 24.0,
    this.color,
    this.strokeWidth = 3.0,
  });

  @override
  Widget build(BuildContext context) {
    final tColor = color ?? context.colores.primario;
    return SizedBox(
      width: size,
      height: size,
      child: CircularProgressIndicator(
        color: tColor,
        strokeWidth: strokeWidth,
      ),
    );
  }
}
