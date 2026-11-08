import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoConstraintWidget extends ElementoBaseWidget {
  const NodoConstraintWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final textoConstraint = (nodo.contenido != null && nodo.contenido!.trim().isNotEmpty)
        ? nodo.contenido!
        : nodo.nombre;

    return envolverPosicion(
      child: Container(
        width: nodo.width > 0 ? nodo.width : 180,
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: const Color(0xFF2D1E1E),
          borderRadius: BorderRadius.circular(5),
          border: Border.all(color: const Color(0xFF8B3A3A), width: 1.2),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.25),
              blurRadius: 5,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '{',
              style: TextStyle(
                color: Color(0xFFEF4444),
                fontSize: 15,
                fontWeight: FontWeight.bold,
                fontFamily: 'monospace',
              ),
            ),
            const SizedBox(width: 4),
            Expanded(
              child: Text(
                textoConstraint,
                style: const TextStyle(
                  color: Color(0xFFFCA5A5),
                  fontSize: 11.5,
                  fontFamily: 'monospace',
                  height: 1.3,
                ),
              ),
            ),
            const SizedBox(width: 4),
            const Text(
              '}',
              style: TextStyle(
                color: Color(0xFFEF4444),
                fontSize: 15,
                fontWeight: FontWeight.bold,
                fontFamily: 'monospace',
              ),
            ),
          ],
        ),
      ),
    );
  }
}

