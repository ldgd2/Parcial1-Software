import 'package:flutter/material.dart';

extension ModificadoresIcono on IconData {
  Widget icono({
    double size = 24, 
    Color? color,
    double? weight,
    double? grade,
    double? opticalSize,
    double? fill,
    String? semanticLabel,
    TextDirection? textDirection,
    List<Shadow>? shadows,
  }) {
    return Icon(
      this,
      size: size,
      color: color,
      weight: weight,
      grade: grade,
      opticalSize: opticalSize,
      fill: fill,
      semanticLabel: semanticLabel,
      textDirection: textDirection,
      shadows: shadows,
    );
  }
}
