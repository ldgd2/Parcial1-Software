import 'package:flutter/material.dart';
import 'package:movil/shared/utils/ui_engine/tema.dart';
import '../base/elemento_base.dart';

class NodoTablaWidget extends ElementoBaseWidget {
  const NodoTablaWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    const accent = Color(0xFF38BDF8);
    final colores = AppColores.oscuro;

    return envolverPosicion(
      child: Container(
        width: nodo.width > 0 ? nodo.width : 220,
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
            // Cabecera tabla
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
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.table_chart_outlined, size: 13, color: accent),
                  const SizedBox(width: 5),
                  const Text(
                    '«table»',
                    style: TextStyle(
                      color: accent,
                      fontSize: 9.5,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      nodo.nombre,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),

            // Columnas de la tabla
            if (nodo.atributos.isNotEmpty) ...[
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: nodo.atributos.map((col) {
                    final isPk = col.visibilidad.toUpperCase() == 'PK';
                    final isFk = col.visibilidad.toUpperCase() == 'FK';

                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2.0),
                      child: Row(
                        children: [
                          if (isPk)
                            const Icon(Icons.vpn_key, size: 11, color: Color(0xFFD4AF37))
                          else if (isFk)
                            const Icon(Icons.link, size: 11, color: Color(0xFF3B82F6))
                          else
                            Text(
                              col.visibilidad,
                              style: TextStyle(
                                color: colores.secundario,
                                fontSize: 10.5,
                                fontFamily: 'monospace',
                              ),
                            ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              '${col.nombre} ${col.tipo}',
                              style: TextStyle(
                                color: isPk ? const Color(0xFFDFD0B8) : Colors.white,
                                fontWeight: isPk ? FontWeight.bold : FontWeight.normal,
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
              ),
            ],

            construirPieResponsable(),
          ],
        ),
      ),
    );
  }
}

