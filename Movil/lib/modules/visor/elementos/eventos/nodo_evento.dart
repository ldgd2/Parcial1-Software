import 'package:flutter/material.dart';
import '../base/elemento_base.dart';

class NodoEventoWidget extends ElementoBaseWidget {
  const NodoEventoWidget({
    super.key,
    required super.nodo,
    required super.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final tipoLower = nodo.type.toLowerCase();
    final isCreate = tipoLower == 'create_event';
    final label = isCreate ? 'Create' : 'Destroy';

    return envolverPosicion(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CustomPaint(
            size: const Size(36, 36),
            painter: _DiamondPainter(
              fillColor: const Color(0xFF6A1B9A),
              strokeColor: const Color(0xFFA855F7),
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: const TextStyle(
              color: Color(0xFFE9D5FF),
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

class _DiamondPainter extends CustomPainter {
  final Color fillColor;
  final Color strokeColor;

  _DiamondPainter({required this.fillColor, required this.strokeColor});

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    final path = Path()
      ..moveTo(w / 2, 0)
      ..lineTo(w, h / 2)
      ..lineTo(w / 2, h)
      ..lineTo(0, h / 2)
      ..close();

    final paintFill = Paint()
      ..color = fillColor
      ..style = PaintingStyle.fill;

    final paintStroke = Paint()
      ..color = strokeColor
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    canvas.drawPath(path, paintFill);
    canvas.drawPath(path, paintStroke);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

