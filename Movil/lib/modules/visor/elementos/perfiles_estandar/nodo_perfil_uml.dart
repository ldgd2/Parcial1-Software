import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoPerfilUmlWidget extends ElementoBaseWidget {
  const NodoPerfilUmlWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  Color _obtenerColor(String tipo) {
    switch (tipo.toLowerCase()) {
      case 'datatype':
        return const Color(0xFFECC94B);
      case 'primitive':
        return const Color(0xFFA3E635);
      case 'signal':
        return const Color(0xFFFACC15);
      case 'artifact':
        return const Color(0xFF38BDF8);
      case 'requirement':
        return const Color(0xFFF97316);
      case 'issue':
        return const Color(0xFFEF4444);
      case 'change':
        return const Color(0xFFF59E0B);
      case 'information_item':
        return const Color(0xFF2DD4BF);
      case 'auxillary':
      case 'focus':
      case 'implementation_class':
      case 'realization_class':
      case 'specification':
      case 'type':
      case 'utility':
        return const Color(0xFF4A7FD4);
      default:
        return const Color(0xFFDFD0B8);
    }
  }

  IconData _obtenerIcono(String tipo) {
    switch (tipo.toLowerCase()) {
      case 'datatype':
        return Icons.data_array;
      case 'primitive':
        return Icons.circle_outlined;
      case 'signal':
        return Icons.bolt;
      case 'artifact':
        return Icons.insert_drive_file_outlined;
      case 'requirement':
        return Icons.checklist;
      case 'issue':
        return Icons.error_outline;
      case 'change':
        return Icons.published_with_changes;
      case 'information_item':
        return Icons.info_outline;
      default:
        return Icons.check_box_outline_blank;
    }
  }

  String _obtenerEstereotipo(String tipo, String? estereotipo) {
    if (estereotipo != null && estereotipo.isNotEmpty) {
      return '«$estereotipo»';
    }
    switch (tipo.toLowerCase()) {
      case 'datatype':
        return '«dataType»';
      case 'primitive':
        return '«primitive»';
      case 'signal':
        return '«signal»';
      case 'artifact':
        return '«artifact»';
      case 'requirement':
        return '«requirement»';
      case 'issue':
        return '«issue»';
      case 'change':
        return '«change»';
      case 'information_item':
        return '«informationItem»';
      case 'auxillary':
        return '«auxillary»';
      case 'focus':
        return '«focus»';
      case 'implementation_class':
        return '«implementationClass»';
      case 'realization_class':
        return '«realization»';
      case 'specification':
        return '«specification»';
      case 'type':
        return '«type»';
      case 'utility':
        return '«utility»';
      default:
        return '«$tipo»';
    }
  }

  @override
  Widget build(BuildContext context) {
    final accent = _obtenerColor(nodo.type);
    final icon = _obtenerIcono(nodo.type);
    final stereotype = _obtenerEstereotipo(nodo.type, nodo.estereotipo);

    return envolverPosicion(
      child: construirContenedorTarjeta(
        context: context,
        accentColor: accent,
        children: [
          construirCabecera(
            estereotipo: stereotype,
            nombre: nodo.nombre,
            accentColor: accent,
            icono: icon,
          ),
          construirCompartimentoAtributos(nodo.atributos),
          construirCompartimentoMetodos(nodo.metodos),
          construirPieResponsable(),
        ],
      ),
    );
  }
}

