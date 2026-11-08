import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoInterfazWidget extends ElementoBaseWidget {
  const NodoInterfazWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    const accent = Color(0xFF60A5FA);

    return envolverPosicion(
      child: construirContenedorTarjeta(
        context: context,
        accentColor: accent,
        children: [
          construirCabecera(
            estereotipo: '«interface»',
            nombre: nodo.nombre,
            accentColor: accent,
            icono: Icons.crop_free,
          ),
          construirCompartimentoAtributos(nodo.atributos),
          construirCompartimentoMetodos(nodo.metodos),
          construirPieResponsable(),
        ],
      ),
    );
  }
}

