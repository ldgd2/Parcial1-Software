import 'package:flutter/material.dart';

extension ModificadoresTexto on String {
  Widget texto({
    double size = 14, 
    bool negrita = false, 
    bool cursiva = false,
    Color? color,
    TextAlign alineacion = TextAlign.left,
    int? maxLineas,
    TextOverflow? overflow,
    TextDecoration? decoracion,
    double? espaciadoLetras,
    double? alturaLinea,
    String? fontFamily,
  }) {
    return Text(
      this,
      textAlign: alineacion,
      maxLines: maxLineas,
      overflow: overflow ?? (maxLineas != null ? TextOverflow.ellipsis : null),
      style: TextStyle(
        fontSize: size,
        fontWeight: negrita ? FontWeight.bold : FontWeight.normal,
        fontStyle: cursiva ? FontStyle.italic : FontStyle.normal,
        color: color,
        decoration: decoracion,
        letterSpacing: espaciadoLetras,
        height: alturaLinea,
        fontFamily: fontFamily,
      ),
    );
  }
}
