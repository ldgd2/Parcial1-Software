import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoClaseWidget extends ElementoBaseWidget {
  const NodoClaseWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    const accent = Color(0xFFDFD0B8);
    final ester = nodo.estereotipo != null && nodo.estereotipo!.isNotEmpty
        ? '«${nodo.estereotipo}»'
        : '«clase»';

    return envolverPosicion(
      child: construirContenedorTarjeta(
        context: context,
        accentColor: accent,
        children: [
          construirCabecera(
            estereotipo: ester,
            nombre: nodo.nombre,
            accentColor: accent,
            icono: Icons.check_box_outline_blank,
          ),
          construirCompartimentoAtributos(nodo.atributos),
          construirCompartimentoMetodos(nodo.metodos),
          construirPieResponsable(),
        ],
      ),
    );
  }
}

