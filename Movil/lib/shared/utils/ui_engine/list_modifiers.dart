import 'package:flutter/material.dart';
import '../../widgets/grids/custom_grid.dart';

extension ListaInteligente on List<Widget> {
  // Si hay espacio, se alinean horizontalmente; si no, saltan a la siguiente línea
  Widget envoltura({double espaciado = 15, WrapAlignment alineacion = WrapAlignment.center}) {
    return Wrap(
      spacing: espaciado, // Espacio horizontal
      runSpacing: espaciado, // Espacio vertical
      alignment: alineacion,
      children: this,
    );
  }
  
  Widget columna({
    double espaciado = 0, 
    MainAxisAlignment mainAxis = MainAxisAlignment.start,
    CrossAxisAlignment crossAxis = CrossAxisAlignment.center,
    MainAxisSize mainAxisSize = MainAxisSize.max,
  }) {
    if (espaciado == 0) {
      return Column(mainAxisAlignment: mainAxis, crossAxisAlignment: crossAxis, mainAxisSize: mainAxisSize, children: this);
    }
    
    return Column(
      mainAxisAlignment: mainAxis, 
      crossAxisAlignment: crossAxis, 
      mainAxisSize: mainAxisSize,
      children: _agregarEspaciado(this, SizedBox(height: espaciado))
    );
  }

  Widget fila({
    double espaciado = 0, 
    MainAxisAlignment mainAxis = MainAxisAlignment.start,
    CrossAxisAlignment crossAxis = CrossAxisAlignment.center,
    MainAxisSize mainAxisSize = MainAxisSize.max,
  }) {
    if (espaciado == 0) {
      return Row(mainAxisAlignment: mainAxis, crossAxisAlignment: crossAxis, mainAxisSize: mainAxisSize, children: this);
    }

    return Row(
      mainAxisAlignment: mainAxis, 
      crossAxisAlignment: crossAxis, 
      mainAxisSize: mainAxisSize,
      children: _agregarEspaciado(this, SizedBox(width: espaciado))
    );
  }

  Widget apilar({
    AlignmentGeometry alineacion = AlignmentDirectional.topStart,
    StackFit ajuste = StackFit.loose,
  }) {
    return Stack(
      alignment: alineacion,
      fit: ajuste,
      children: this,
    );
  }

  Widget listaScroll({
    Axis direccion = Axis.vertical,
    EdgeInsetsGeometry? padding,
    bool shrinkWrap = false,
  }) {
    return ListView(
      scrollDirection: direccion,
      padding: padding,
      shrinkWrap: shrinkWrap,
      children: this,
    );
  }

  /// Convierte cualquier lista de widgets en una cuadrícula (Grid) responsiva
  Widget cuadricula({
    int columnas = 2,
    double espaciado = 12.0,
    double proporcionAspecto = 1.0,
    EdgeInsetsGeometry padding = EdgeInsets.zero,
    bool shrinkWrap = true,
    ScrollPhysics? physics = const NeverScrollableScrollPhysics(),
  }) {
    return CustomGrid.count(
      crossAxisCount: columnas,
      spacing: espaciado,
      childAspectRatio: proporcionAspecto,
      padding: padding,
      shrinkWrap: shrinkWrap,
      physics: physics,
      children: this,
    );
  }

  List<Widget> _agregarEspaciado(List<Widget> items, Widget espaciador) {
    if (items.isEmpty) return items;
    final List<Widget> conEspacios = [];
    for (int i = 0; i < items.length; i++) {
      conEspacios.add(items[i]);
      if (i != items.length - 1) {
        conEspacios.add(espaciador);
      }
    }
    return conEspacios;
  }
}
