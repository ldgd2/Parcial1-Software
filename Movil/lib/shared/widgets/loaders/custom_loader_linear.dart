import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Indicador de progreso lineal abstracto.
/// Soporta progreso determinado (valor) o indeterminado.
class CustomLoaderLinear extends StatelessWidget {
  final double? value; // Si es nulo, es indeterminado
  final Color? backgroundColor;
  final Color? color;
  final double minHeight;
  final double borderRadius;

  const CustomLoaderLinear({
    super.key,
    this.value,
    this.backgroundColor,
    this.color,
    this.minHeight = 6.0,
    this.borderRadius = 8.0,
  });

  @override
  Widget build(BuildContext context) {
    final tColor = color ?? context.colores.primario;
    final tBgColor = backgroundColor ?? context.colores.fondoSecundario;

    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: LinearProgressIndicator(
        value: value,
        backgroundColor: tBgColor,
        color: tColor,
        minHeight: minHeight,
      ),
    );
  }
}
