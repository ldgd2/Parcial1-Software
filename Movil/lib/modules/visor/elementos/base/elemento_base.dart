import 'package:flutter/material.dart';
import 'package:movil/modules/visor/models/lienzo_model.dart';
import 'package:movil/shared/utils/ui_engine/tema.dart';

abstract class ElementoBaseWidget extends StatelessWidget {
  final NodoModel nodo;
  final VoidCallback onTap;

  const ElementoBaseWidget({
    super.key,
    required this.nodo,
    required this.onTap,
  });

  Widget envolverPosicion({
    required Widget child,
    double? customWidth,
    double? customHeight,
  }) {
    return Positioned(
      left: nodo.x,
      top: nodo.y,
      child: GestureDetector(
        onTap: onTap,
        child: child,
      ),
    );
  }

  Widget construirContenedorTarjeta({
    required BuildContext context,
    required Color accentColor,
    required List<Widget> children,
    double defaultWidth = 220,
  }) {
    final colores = AppColores.oscuro;
    final w = nodo.width > 0 ? nodo.width : defaultWidth;

    return Container(
      width: w,
      decoration: BoxDecoration(
        color: colores.fondoSecundario,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: accentColor.withValues(alpha: 0.6), width: 1.4),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.35),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: children,
      ),
    );
  }

  Widget construirCabecera({
    required String estereotipo,
    required String nombre,
    required Color accentColor,
    required IconData icono,
    bool esItalica = false,
  }) {
    final colores = AppColores.oscuro;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: colores.fondo,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(4.6),
          topRight: Radius.circular(4.6),
        ),
        border: Border(
          bottom: BorderSide(color: colores.borde, width: 1),
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icono, size: 12, color: accentColor),
              const SizedBox(width: 4),
              Text(
                estereotipo,
                style: TextStyle(
                  color: accentColor,
                  fontSize: 9.5,
                  fontStyle: FontStyle.italic,
                  letterSpacing: 0.3,
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Text(
            nombre,
            style: TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontWeight: FontWeight.bold,
              fontStyle: esItalica ? FontStyle.italic : FontStyle.normal,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget construirCompartimentoAtributos(List<AtributoModel> atributos) {
    if (atributos.isEmpty) return const SizedBox.shrink();
    final colores = AppColores.oscuro;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: colores.borde, width: 0.8),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: atributos.map((attr) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 1.5),
            child: Row(
              children: [
                Text(
                  attr.visibilidad,
                  style: TextStyle(
                    color: colores.primario,
                    fontWeight: FontWeight.bold,
                    fontSize: 10.5,
                    fontFamily: 'monospace',
                  ),
                ),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    '${attr.nombre}: ${attr.tipo}',
                    style: const TextStyle(
                      color: Color(0xFFDFD0B8),
                      fontSize: 11,
                      fontFamily: 'monospace',
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget construirCompartimentoMetodos(List<MetodoModel> metodos) {
    if (metodos.isEmpty) return const SizedBox.shrink();
    final colores = AppColores.oscuro;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: metodos.map((met) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 1.5),
            child: Row(
              children: [
                Text(
                  met.visibilidad,
                  style: TextStyle(
                    color: colores.primario,
                    fontWeight: FontWeight.bold,
                    fontSize: 10.5,
                    fontFamily: 'monospace',
                  ),
                ),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    '${met.nombre}(${met.parametros}): ${met.retorno}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontFamily: 'monospace',
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget construirPieResponsable() {
    if (nodo.responsable == null || nodo.responsable!.isEmpty) {
      return const SizedBox.shrink();
    }
    final colores = AppColores.oscuro;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
      decoration: BoxDecoration(
        color: colores.fondo,
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(4.6),
          bottomRight: Radius.circular(4.6),
        ),
        border: Border(top: BorderSide(color: colores.borde)),
      ),
      child: Row(
        children: [
          Icon(Icons.person_outline, size: 11, color: colores.primario),
          const SizedBox(width: 4),
          Expanded(
            child: Text(
              nodo.responsable!,
              style: TextStyle(
                color: colores.primario,
                fontSize: 9.5,
                fontWeight: FontWeight.w600,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

