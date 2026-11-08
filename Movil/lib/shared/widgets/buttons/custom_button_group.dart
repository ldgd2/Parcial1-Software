import 'package:flutter/material.dart';

/// Un contenedor inteligente para abstraer la agrupación de botones.
/// Reemplaza la necesidad de escribir Rows, Columns, SizedBox y Expanded manualmente.
class CustomButtonGroup extends StatelessWidget {
  /// Lista de botones a agrupar.
  final List<Widget> buttons;
  
  /// Dirección en la que se apilan los botones (horizontal o vertical).
  final Axis direction;
  
  /// Espacio exacto entre cada botón.
  final double spacing;
  
  /// Si es true:
  /// - En modo horizontal: Hace que los botones tengan el mismo ancho (Expanded).
  /// - En modo vertical: Hace que los botones ocupen todo el ancho posible (Stretch).
  final bool expandButtons;
  
  /// Alineación cuando expandButtons es false.
  final MainAxisAlignment mainAxisAlignment;

  const CustomButtonGroup({
    super.key,
    required this.buttons,
    this.direction = Axis.horizontal,
    this.spacing = 16.0,
    this.expandButtons = true,
    this.mainAxisAlignment = MainAxisAlignment.center,
  });

  @override
  Widget build(BuildContext context) {
    if (buttons.isEmpty) return const SizedBox.shrink();

    final List<Widget> spacedChildren = [];

    for (int i = 0; i < buttons.length; i++) {
      Widget child = buttons[i];
      
      // Expandimos horizontalmente solo si es una Row
      if (expandButtons && direction == Axis.horizontal) {
        child = Expanded(child: child);
      }
      
      spacedChildren.add(child);

      // Añadir espacio entre botones (excepto en el último)
      if (i < buttons.length - 1) {
        spacedChildren.add(
          SizedBox(
            width: direction == Axis.horizontal ? spacing : 0,
            height: direction == Axis.vertical ? spacing : 0,
          ),
        );
      }
    }

    if (direction == Axis.horizontal) {
      return Row(
        mainAxisAlignment: mainAxisAlignment,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: spacedChildren,
      );
    } else {
      return Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: mainAxisAlignment,
        crossAxisAlignment: expandButtons 
            ? CrossAxisAlignment.stretch 
            : CrossAxisAlignment.center,
        children: spacedChildren,
      );
    }
  }
}
