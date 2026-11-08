import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoPartWidget extends ElementoBaseWidget {
  const NodoPartWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return envolverPosicion(
      child: Container(
        width: nodo.width > 0 ? nodo.width : 190,
        height: 56,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: const Color(0xFF3B82F6), width: 1.4),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.3),
              blurRadius: 6,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.widgets_outlined, size: 16, color: Color(0xFF60A5FA)),
            const SizedBox(width: 8),
            Flexible(
              child: Text(
                nodo.nombre,
                style: const TextStyle(
                  color: Color(0xFF93C5FD),
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

