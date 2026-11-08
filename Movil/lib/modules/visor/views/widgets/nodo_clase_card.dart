import 'package:flutter/material.dart';
import 'package:movil/modules/visor/models/lienzo_model.dart';
import 'package:movil/modules/visor/elementos/base/elemento_factory.dart';

class NodoClaseCard extends StatelessWidget {
  final NodoModel nodo;
  final VoidCallback onTap;

  const NodoClaseCard({
    super.key,
    required this.nodo,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ElementoFactory.crear(nodo: nodo, onTap: onTap);
  }
}
