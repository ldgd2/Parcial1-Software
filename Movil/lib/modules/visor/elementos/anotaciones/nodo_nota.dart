import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoNotaWidget extends ElementoBaseWidget {
  const NodoNotaWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final tieneContenido = nodo.contenido != null && nodo.contenido!.trim().isNotEmpty;
    final nombreEsGenerico = nodo.nombre == 'NuevaClase' ||
        nodo.nombre == 'Nueva Clase' ||
        nodo.nombre == 'Clase' ||
        nodo.nombre.isEmpty;

    final textoNota = tieneContenido
        ? nodo.contenido!
        : (!nombreEsGenerico ? nodo.nombre : 'Nota');

    return envolverPosicion(
      child: Container(
        width: nodo.width > 0 ? nodo.width : 200,
        constraints: const BoxConstraints(minHeight: 80),
        padding: const EdgeInsets.fromLTRB(14, 12, 16, 12),
        decoration: BoxDecoration(
          color: const Color(0xFF2A2510),
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(3),
            topRight: Radius.circular(12),
            bottomLeft: Radius.circular(4),
            bottomRight: Radius.circular(4),
          ),
          border: Border.all(color: const Color(0xFF7A6A20), width: 1.2),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.3),
              blurRadius: 6,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Stack(
          children: [
            Positioned(
              top: -12,
              right: -16,
              child: CustomPaint(
                size: const Size(14, 14),
                painter: _DogEarPainter(),
              ),
            ),
            Text(
              textoNota,
              style: const TextStyle(
                color: Color(0xFFD4C57A),
                fontSize: 12,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DogEarPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..moveTo(0, size.height)
      ..lineTo(size.width, 0)
      ..lineTo(0, 0)
      ..close();

    final paintFold = Paint()
      ..color = const Color(0xFF7A6A20)
      ..style = PaintingStyle.fill;

    canvas.drawPath(path, paintFold);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

