import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoAbstractaWidget extends ElementoBaseWidget {
  const NodoAbstractaWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    const accent = Color(0xFFF59E0B);

    return envolverPosicion(
      child: construirContenedorTarjeta(
        context: context,
        accentColor: accent,
        children: [
          construirCabecera(
            estereotipo: '«abstracta»',
            nombre: nodo.nombre,
            accentColor: accent,
            icono: Icons.functions,
            esItalica: true,
          ),
          construirCompartimentoAtributos(nodo.atributos),
          construirCompartimentoMetodos(nodo.metodos),
          construirPieResponsable(),
        ],
      ),
    );
  }
}

