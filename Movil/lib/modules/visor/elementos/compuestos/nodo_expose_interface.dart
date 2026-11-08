import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoExposeInterfaceWidget extends ElementoBaseWidget {
  const NodoExposeInterfaceWidget({
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
            width: 22,
            height: 22,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFFCBD5E1),
              border: Border.all(color: const Color(0xFF64748B), width: 2),
            ),
          ),
          const SizedBox(width: 6),
          Text(
            nodo.nombre,
            style: const TextStyle(
              color: Color(0xFFE2E8F0),
              fontSize: 11.5,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

