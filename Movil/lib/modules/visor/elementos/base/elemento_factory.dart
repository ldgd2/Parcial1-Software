import 'package:flutter/material.dart';
import 'package:movil/modules/visor/models/lienzo_model.dart';
import '../estructurales/nodo_clase.dart';
import '../estructurales/nodo_interfaz.dart';
import '../estructurales/nodo_abstracta.dart';
import '../estructurales/nodo_enum.dart';
import '../anotaciones/nodo_nota.dart';
import '../anotaciones/nodo_constraint.dart';
import '../anotaciones/nodo_texto.dart';
import '../compuestos/nodo_part.dart';
import '../compuestos/nodo_port.dart';
import '../compuestos/nodo_expose_interface.dart';
import '../compuestos/nodo_boundary.dart';
import '../base_datos/nodo_tabla.dart';
import '../eventos/nodo_evento.dart';
import '../perfiles_estandar/nodo_perfil_uml.dart';

class ElementoFactory {
  static Widget crear({
    required NodoModel nodo,
    required VoidCallback onTap,
  }) {
    final tipoLower = nodo.type.toLowerCase();
    final esterLower = (nodo.estereotipo ?? '').toLowerCase();

    // 1. Anotaciones
    if (tipoLower == 'note' || esterLower == 'note') {
      return NodoNotaWidget(nodo: nodo, onTap: onTap);
    }
    if (tipoLower == 'constraint') {
      return NodoConstraintWidget(nodo: nodo, onTap: onTap);
    }
    if (tipoLower == 'text') {
      return NodoTextoWidget(nodo: nodo, onTap: onTap);
    }

    // 2. Compuestos
    if (tipoLower == 'part') {
      return NodoPartWidget(nodo: nodo, onTap: onTap);
    }
    if (tipoLower == 'port') {
      return NodoPortWidget(nodo: nodo, onTap: onTap);
    }
    if (tipoLower == 'expose_interface') {
      return NodoExposeInterfaceWidget(nodo: nodo, onTap: onTap);
    }
    if (tipoLower == 'boundary') {
      return NodoBoundaryWidget(nodo: nodo, onTap: onTap);
    }

    // 3. Eventos
    if (tipoLower == 'create_event' || tipoLower == 'destroy_event') {
      return NodoEventoWidget(nodo: nodo, onTap: onTap);
    }

    // 4. Base de datos
    if (esterLower == 'table') {
      return NodoTablaWidget(nodo: nodo, onTap: onTap);
    }

    // 5. Estructurales
    if (tipoLower == 'enum') {
      return NodoEnumWidget(nodo: nodo, onTap: onTap);
    }
    if (tipoLower == 'interface') {
      return NodoInterfazWidget(nodo: nodo, onTap: onTap);
    }
    if (tipoLower == 'abstract') {
      return NodoAbstractaWidget(nodo: nodo, onTap: onTap);
    }

    // 6. Perfiles Estándar UML
    const perfilesUml = [
      'datatype',
      'primitive',
      'signal',
      'artifact',
      'requirement',
      'issue',
      'change',
      'information_item',
      'auxillary',
      'focus',
      'implementation_class',
      'realization_class',
      'specification',
      'type',
      'utility',
    ];

    if (perfilesUml.contains(tipoLower)) {
      return NodoPerfilUmlWidget(nodo: nodo, onTap: onTap);
    }

    // 7. Clase por defecto
    return NodoClaseWidget(nodo: nodo, onTap: onTap);
  }
}

