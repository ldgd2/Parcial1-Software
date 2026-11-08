import 'package:flutter/material.dart';
import 'package:movil/shared/utils/ui_engine/tema.dart';
import '../base/elemento_base.dart';

class NodoEnumWidget extends ElementoBaseWidget {
  const NodoEnumWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    const accent = Color(0xFF34D399);
    final colores = AppColores.oscuro;

    return envolverPosicion(
      child: Container(
        width: nodo.width > 0 ? nodo.width : 200,
        decoration: BoxDecoration(
          color: colores.fondoSecundario,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: accent.withValues(alpha: 0.6), width: 1.4),
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
          children: [
            // Cabecera Enum
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
              decoration: BoxDecoration(
                color: colores.fondo,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(4.6),
                  topRight: Radius.circular(4.6),
                ),
                border: Border(bottom: BorderSide(color: colores.borde, width: 1)),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Icon(Icons.format_list_bulleted, size: 12, color: accent),
                      SizedBox(width: 4),
                      Text(
                        '«enum»',
                        style: TextStyle(
                          color: accent,
                          fontSize: 9.5,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    nodo.nombre,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),

            // Compartimento de Valores
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: nodo.valores.map((v) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2.0),
                    child: Text(
                      v,
                      style: const TextStyle(
                        color: Color(0xFF34D399),
                        fontSize: 11,
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),

            construirPieResponsable(),
          ],
        ),
      ),
    );
  }
}

