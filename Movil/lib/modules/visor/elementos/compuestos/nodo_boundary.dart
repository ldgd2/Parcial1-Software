import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoBoundaryWidget extends ElementoBaseWidget {
  const NodoBoundaryWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return envolverPosicion(
      child: Container(
        width: nodo.width > 0 ? nodo.width : 320,
        height: nodo.height > 0 ? nodo.height : 220,
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.02),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: const Color(0xFF64748B), width: 1.5),
        ),
        padding: const EdgeInsets.all(10),
        child: Align(
          alignment: Alignment.topLeft,
          child: Text(
            nodo.nombre,
            style: const TextStyle(
              color: Color(0xFF94A3B8),
              fontSize: 13,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }
}

