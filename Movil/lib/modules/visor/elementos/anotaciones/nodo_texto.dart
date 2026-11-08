import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoTextoWidget extends ElementoBaseWidget {
  const NodoTextoWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final textoLibre = (nodo.contenido != null && nodo.contenido!.trim().isNotEmpty)
        ? nodo.contenido!
        : nodo.nombre;

    return envolverPosicion(
      child: Container(
        width: nodo.width > 0 ? nodo.width : 180,
        padding: const EdgeInsets.all(6),
        decoration: BoxDecoration(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(4),
          border: Border.all(
            color: const Color(0xFF475569).withValues(alpha: 0.4),
            style: BorderStyle.solid,
          ),
        ),
        child: Text(
          textoLibre,
          style: const TextStyle(
            color: Color(0xFFE2E8F0),
            fontSize: 12,
            height: 1.3,
          ),
        ),
      ),
    );
  }
}

