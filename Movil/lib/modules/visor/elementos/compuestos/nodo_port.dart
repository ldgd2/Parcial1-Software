import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoPortWidget extends ElementoBaseWidget {
  const NodoPortWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return envolverPosicion(
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 26,
            height: 26,
            decoration: BoxDecoration(
              color: const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(3),
              border: Border.all(color: const Color(0xFF3B82F6), width: 1.5),
            ),
            child: const Icon(Icons.crop_square, size: 14, color: Color(0xFF60A5FA)),
          ),
          const SizedBox(width: 6),
          Text(
            nodo.nombre,
            style: const TextStyle(
              color: Color(0xFF93C5FD),
              fontSize: 11,
              fontFamily: 'monospace',
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

