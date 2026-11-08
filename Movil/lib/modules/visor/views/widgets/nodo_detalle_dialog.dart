import 'package:flutter/material.dart';
import 'package:movil/shared/utils/ui_engine/tema.dart';
import 'package:movil/modules/visor/models/lienzo_model.dart';

class NodoDetalleDialog extends StatelessWidget {
  final NodoModel nodo;

  const NodoDetalleDialog({super.key, required this.nodo});

  @override
  Widget build(BuildContext context) {
    final colores = AppColores.oscuro;
    final textos = AppTextos.generar(colores);

    final tipoLower = nodo.type.toLowerCase();
    final esterLower = (nodo.estereotipo ?? '').toLowerCase();

    final esNota = tipoLower == 'note' || esterLower == 'note';
    final esConstraint = tipoLower == 'constraint';
    final esTexto = tipoLower == 'text';
    final esBoundary = tipoLower == 'boundary';
    final esPart = tipoLower == 'part';
    final esPort = tipoLower == 'port';
    final esExposeInterface = tipoLower == 'expose_interface';
    final esEvento = tipoLower == 'create_event' || tipoLower == 'destroy_event';
    final esEnum = tipoLower == 'enum';
    final esTabla = esterLower == 'table';

    final tieneContenido = nodo.contenido != null && nodo.contenido!.trim().isNotEmpty;
    final nombreEsGenerico = nodo.nombre == 'NuevaClase' ||
        nodo.nombre == 'Nueva Clase' ||
        nodo.nombre == 'Clase' ||
        nodo.nombre.isEmpty;

    String tituloElemento = nodo.nombre;
    if (esNota) {
      tituloElemento = tieneContenido
          ? (nodo.contenido!.length > 30 ? '${nodo.contenido!.substring(0, 30)}...' : nodo.contenido!)
          : (!nombreEsGenerico ? nodo.nombre : 'Nota');
    } else if (esConstraint) {
      tituloElemento = tieneContenido
          ? '{ ${nodo.contenido!} }'
          : '{ ${nodo.nombre} }';
    } else if (esTexto) {
      tituloElemento = tieneContenido ? nodo.contenido! : nodo.nombre;
    } else if (esEvento) {
      tituloElemento = tipoLower == 'create_event' ? 'Create Event' : 'Destroy Event';
    }

    IconData iconoEncabezado = Icons.data_object;
    if (esNota) {
      iconoEncabezado = Icons.sticky_note_2_outlined;
    } else if (esConstraint) {
      iconoEncabezado = Icons.code;
    } else if (esTexto) {
      iconoEncabezado = Icons.text_fields;
    } else if (esBoundary) {
      iconoEncabezado = Icons.crop_free;
    } else if (esPart) {
      iconoEncabezado = Icons.widgets_outlined;
    } else if (esPort) {
      iconoEncabezado = Icons.crop_square;
    } else if (esExposeInterface) {
      iconoEncabezado = Icons.radio_button_checked;
    } else if (esEvento) {
      iconoEncabezado = Icons.diamond_outlined;
    } else if (esEnum) {
      iconoEncabezado = Icons.format_list_bulleted;
    } else if (esTabla) {
      iconoEncabezado = Icons.table_chart_outlined;
    }

    final tipoMostrar = esTabla ? 'TABLA DB' : nodo.type.toUpperCase();

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.75,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: colores.fondoSecundario,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
        border: Border.all(color: colores.borde),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Drag handle
          Center(
            child: Container(
              width: 36,
              height: 4,
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                color: colores.secundario.withOpacity(0.4),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          // Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: colores.fondo,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  iconoEncabezado,
                  color: colores.primario,
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      tituloElemento,
                      style: textos.titulo.copyWith(fontSize: 16),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      'Tipo: $tipoMostrar • Versión ${nodo.version}',
                      style: textos.cuerpoPequeno.copyWith(color: colores.secundario),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: colores.fondo,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: colores.borde),
                ),
                child: Text(
                  'v${nodo.version}',
                  style: textos.cuerpoPequeno.copyWith(
                    color: colores.primario,
                    fontWeight: FontWeight.bold,
                    fontSize: 11,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),
          const Divider(height: 1, color: Color(0xFF222831)),
          const SizedBox(height: 12),

          Expanded(
            child: ListView(
              children: [
                // ── NOTA ──
                if (esNota) ...[
                  _seccionTitulo('Contenido de la nota', colores),
                  Container(
                    margin: const EdgeInsets.only(bottom: 14),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF2A2510),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFF7A6A20)),
                    ),
                    child: Text(
                      nodo.contenido ?? (!nombreEsGenerico ? nodo.nombre : 'Sin contenido'),
                      style: const TextStyle(
                        color: Color(0xFFD4C57A),
                        fontSize: 13,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],

                // ── CONSTRAINT ──
                if (esConstraint) ...[
                  _seccionTitulo('Expresión de Restricción', colores),
                  Container(
                    margin: const EdgeInsets.only(bottom: 14),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF2D1E1E),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFF8B3A3A)),
                    ),
                    child: Text(
                      '{ ${nodo.contenido ?? nodo.nombre} }',
                      style: const TextStyle(
                        color: Color(0xFFFCA5A5),
                        fontSize: 13,
                        fontFamily: 'monospace',
                        height: 1.4,
                      ),
                    ),
                  ),
                ],

                // ── TEXTO LIBRE ──
                if (esTexto) ...[
                  _seccionTitulo('Texto', colores),
                  Container(
                    margin: const EdgeInsets.only(bottom: 14),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: colores.fondo,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: colores.borde),
                    ),
                    child: Text(
                      nodo.contenido ?? nodo.nombre,
                      style: const TextStyle(
                        color: Color(0xFFE2E8F0),
                        fontSize: 13,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],

                // ── ENUM VALORES ──
                if (esEnum) ...[
                  _seccionTitulo('Valores (${nodo.valores.length})', colores),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: nodo.valores.map((v) {
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: colores.fondo,
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: colores.borde),
                        ),
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
                  const SizedBox(height: 12),
                ],

                // ── TABLA DE BASE DE DATOS (COLUMNAS) ──
                if (esTabla) ...[
                  _seccionTitulo('Columnas (${nodo.atributos.length})', colores),
                  ...nodo.atributos.map((col) {
                    final isPk = col.visibilidad.toUpperCase() == 'PK';
                    final isFk = col.visibilidad.toUpperCase() == 'FK';
                    return Container(
                      margin: const EdgeInsets.only(bottom: 4),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: colores.fondo,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Row(
                        children: [
                          if (isPk)
                            const Icon(Icons.vpn_key, size: 12, color: Color(0xFFD4AF37))
                          else if (isFk)
                            const Icon(Icons.link, size: 12, color: Color(0xFF3B82F6))
                          else
                            Text(
                              col.visibilidad,
                              style: TextStyle(color: colores.secundario, fontFamily: 'monospace'),
                            ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              col.nombre,
                              style: TextStyle(
                                color: isPk ? const Color(0xFFDFD0B8) : Colors.white,
                                fontWeight: isPk ? FontWeight.bold : FontWeight.normal,
                                fontSize: 13,
                              ),
                            ),
                          ),
                          Text(
                            col.tipo,
                            style: TextStyle(
                              color: colores.secundario,
                              fontSize: 12,
                              fontFamily: 'monospace',
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                  const SizedBox(height: 12),
                ],

                // ── RESPONSABLE Y RESPONSABILIDADES ──
                if (nodo.responsable != null && nodo.responsable!.isNotEmpty) ...[
                  _seccionTitulo('Responsable Asignado', colores),
                  Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: colores.fondo,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.person, color: colores.primario, size: 18),
                        const SizedBox(width: 8),
                        Text(
                          nodo.responsable!,
                          style: TextStyle(color: colores.primario, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                ],

                if (nodo.responsabilidades.isNotEmpty) ...[
                  _seccionTitulo('Responsabilidades / Habilidades Requeridas', colores),
                  ...nodo.responsabilidades.map((resp) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2.0),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.check, size: 14, color: colores.exito),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(resp, style: textos.cuerpoPequeno),
                          ),
                        ],
                      ),
                    );
                  }),
                  const SizedBox(height: 12),
                ],

                // ── ATRIBUTOS Y MÉTODOS PARA CLASES / INTERFACES ──
                if (!esNota && !esConstraint && !esTexto && !esBoundary && !esPart && !esPort && !esExposeInterface && !esEvento && !esEnum && !esTabla) ...[
                  // Atributos
                  _seccionTitulo('Atributos (${nodo.atributos.length})', colores),
                  if (nodo.atributos.isEmpty)
                    Text('Sin atributos declarados.', style: textos.cuerpoPequeno.copyWith(color: colores.secundario))
                  else
                    ...nodo.atributos.map((attr) {
                      return Container(
                        margin: const EdgeInsets.only(bottom: 4),
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: colores.fondo,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 24,
                              alignment: Alignment.center,
                              child: Text(
                                attr.visibilidad,
                                style: TextStyle(
                                  color: colores.primario,
                                  fontWeight: FontWeight.bold,
                                  fontFamily: 'monospace',
                                ),
                              ),
                            ),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                attr.nombre,
                                style: const TextStyle(color: Colors.white, fontSize: 13),
                              ),
                            ),
                            Text(
                              attr.tipo,
                              style: TextStyle(
                                color: colores.secundario,
                                fontSize: 12,
                                fontFamily: 'monospace',
                              ),
                            ),
                          ],
                        ),
                      );
                    }),

                  const SizedBox(height: 14),

                  // Métodos
                  _seccionTitulo('Métodos (${nodo.metodos.length})', colores),
                  if (nodo.metodos.isEmpty)
                    Text('Sin métodos declarados.', style: textos.cuerpoPequeno.copyWith(color: colores.secundario))
                  else
                    ...nodo.metodos.map((met) {
                      return Container(
                        margin: const EdgeInsets.only(bottom: 4),
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: colores.fondo,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 24,
                              alignment: Alignment.center,
                              child: Text(
                                met.visibilidad,
                                style: TextStyle(
                                  color: colores.primario,
                                  fontWeight: FontWeight.bold,
                                  fontFamily: 'monospace',
                                ),
                              ),
                            ),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                '${met.nombre}(${met.parametros})',
                                style: const TextStyle(color: Colors.white, fontSize: 13),
                              ),
                            ),
                            Text(
                              met.retorno,
                              style: TextStyle(
                                color: colores.secundario,
                                fontSize: 12,
                                fontFamily: 'monospace',
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                ],
              ],
            ),
          ),

          const SizedBox(height: 12),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: colores.fondo,
              foregroundColor: colores.primario,
              side: BorderSide(color: colores.borde),
            ),
            onPressed: () => Navigator.pop(context),
            child: const Text('Cerrar'),
          ),
        ],
      ),
    );
  }

  Widget _seccionTitulo(String titulo, AppColores colores) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6.0),
      child: Text(
        titulo,
        style: TextStyle(
          color: colores.primario,
          fontSize: 12,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.3,
        ),
      ),
    );
  }
}
