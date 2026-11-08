import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../models/lienzo_model.dart';

class RelacionesPainter extends CustomPainter {
  final List<RelacionModel> relaciones;
  final Map<String, NodoModel> nodosMap;
  final Color colorLinea;
  final Color colorTexto;

  RelacionesPainter({
    required this.relaciones,
    required this.nodosMap,
    required this.colorLinea,
    required this.colorTexto,
  });

  Offset _borderPoint(NodoModel node, double toX, double toY) {
    final cx = node.x + (node.width / 2);
    final cy = node.y + (node.height / 2);
    final dx = toX - cx;
    final dy = toY - cy;
    final hw = node.width / 2;
    final hh = node.height / 2;

    if (dx == 0 && dy == 0) return Offset(cx, node.y);

    if ((dx.abs() * hh) > (dy.abs() * hw)) {
      final side = dx > 0 ? hw : -hw;
      return Offset(cx + side, cy + (side / dx) * dy);
    } else {
      final side = dy > 0 ? hh : -hh;
      return Offset(cx + (side / dy) * dx, cy + side);
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    final paintLinea = Paint()
      ..color = colorLinea
      ..strokeWidth = 1.6
      ..style = PaintingStyle.stroke;

    final paintRelleno = Paint()
      ..color = colorLinea
      ..style = PaintingStyle.fill;

    for (final rel in relaciones) {
      final source = nodosMap[rel.sourceId];
      final target = nodosMap[rel.targetId];

      if (source == null || target == null) continue;

      // Calcular centros y luego intersección exacta en los bordes de cada nodo
      final cSource = Offset(source.x + (source.width / 2), source.y + (source.height / 2));
      final cTarget = Offset(target.x + (target.width / 2), target.y + (target.height / 2));

      final p1 = _borderPoint(source, cTarget.dx, cTarget.dy);
      final p2 = _borderPoint(target, cSource.dx, cSource.dy);

      // Dibujar línea (discontinua si es dependencia, realización o enlace)
      final typeLower = rel.type.toLowerCase();
      final esPunteada = typeLower == 'dependency' ||
          typeLower == 'realization' ||
          typeLower == 'template_binding' ||
          typeLower == 'usage' ||
          typeLower == 'association_class';

      if (esPunteada) {
        _dibujarLineaPunteada(canvas, p1, p2, paintLinea);
      } else {
        canvas.drawLine(p1, p2, paintLinea);
      }

      // Dibujar símbolo de relación en el extremo de destino
      _dibujarExtremoRelacion(canvas, p1, p2, typeLower, paintLinea, paintRelleno);

      // Multiplicidad de origen
      if (rel.sourceMultiplicity != null && rel.sourceMultiplicity!.isNotEmpty) {
        final dx = p2.dx - p1.dx;
        final dy = p2.dy - p1.dy;
        final dist = math.sqrt(dx * dx + dy * dy);
        if (dist > 30) {
          final ux = dx / dist;
          final uy = dy / dist;
          final pSrcLabel = Offset(p1.dx + ux * 22, p1.dy + uy * 22 - 10);
          _dibujarTexto(canvas, rel.sourceMultiplicity!, pSrcLabel.dx, pSrcLabel.dy);
        }
      }

      // Multiplicidad de destino
      if (rel.targetMultiplicity != null && rel.targetMultiplicity!.isNotEmpty) {
        final dx = p2.dx - p1.dx;
        final dy = p2.dy - p1.dy;
        final dist = math.sqrt(dx * dx + dy * dy);
        if (dist > 30) {
          final ux = dx / dist;
          final uy = dy / dist;
          final pTgtLabel = Offset(p2.dx - ux * 22, p2.dy - uy * 22 - 10);
          _dibujarTexto(canvas, rel.targetMultiplicity!, pTgtLabel.dx, pTgtLabel.dy);
        }
      }

      // Etiqueta central de la relación
      if (rel.label != null && rel.label!.isNotEmpty) {
        final mid = Offset((p1.dx + p2.dx) / 2, (p1.dy + p2.dy) / 2);
        _dibujarTexto(canvas, rel.label!, mid.dx, mid.dy - 12);
      }
    }
  }

  void _dibujarLineaPunteada(Canvas canvas, Offset p1, Offset p2, Paint paint) {
    const dashWidth = 6.0;
    const dashSpace = 4.0;
    final dx = p2.dx - p1.dx;
    final dy = p2.dy - p1.dy;
    final distance = math.sqrt(dx * dx + dy * dy);
    if (distance == 0) return;

    final ux = dx / distance;
    final uy = dy / distance;
    double current = 0.0;

    while (current < distance) {
      final start = Offset(p1.dx + ux * current, p1.dy + uy * current);
      final endLength = math.min(dashWidth, distance - current);
      final end = Offset(start.dx + ux * endLength, start.dy + uy * endLength);
      canvas.drawLine(start, end, paint);
      current += dashWidth + dashSpace;
    }
  }

  void _dibujarExtremoRelacion(
    Canvas canvas,
    Offset p1,
    Offset p2,
    String type,
    Paint paintLinea,
    Paint paintRelleno,
  ) {
    final angle = math.atan2(p2.dy - p1.dy, p2.dx - p1.dx);
    const arrowSize = 13.0;

    canvas.save();
    canvas.translate(p2.dx, p2.dy);
    canvas.rotate(angle);

    if (type == 'inheritance' || type == 'realization') {
      // Triángulo hueco
      final path = Path()
        ..moveTo(0, 0)
        ..lineTo(-arrowSize, -arrowSize / 2)
        ..lineTo(-arrowSize, arrowSize / 2)
        ..close();
      final paintHueco = Paint()
        ..color = const Color(0xFF222831)
        ..style = PaintingStyle.fill;
      canvas.drawPath(path, paintHueco);
      canvas.drawPath(path, paintLinea);
    } else if (type == 'composition' || type == 'composition_to_whole' || type == 'composition_to_part') {
      // Rombo relleno
      final path = Path()
        ..moveTo(0, 0)
        ..lineTo(-arrowSize / 1.5, -arrowSize / 2.5)
        ..lineTo(-arrowSize * 1.3, 0)
        ..lineTo(-arrowSize / 1.5, arrowSize / 2.5)
        ..close();
      canvas.drawPath(path, paintRelleno);
    } else if (type == 'aggregation' || type == 'aggregation_to_whole' || type == 'aggregation_to_part') {
      // Rombo vacío
      final path = Path()
        ..moveTo(0, 0)
        ..lineTo(-arrowSize / 1.5, -arrowSize / 2.5)
        ..lineTo(-arrowSize * 1.3, 0)
        ..lineTo(-arrowSize / 1.5, arrowSize / 2.5)
        ..close();
      final paintHueco = Paint()
        ..color = const Color(0xFF222831)
        ..style = PaintingStyle.fill;
      canvas.drawPath(path, paintHueco);
      canvas.drawPath(path, paintLinea);
    } else if (type == 'association' || type == 'directed' || type == 'dependency' || type.contains(':')) {
      // Flecha simple para asociación o relación DB
      final path = Path()
        ..moveTo(-arrowSize, -arrowSize / 2.5)
        ..lineTo(0, 0)
        ..lineTo(-arrowSize, arrowSize / 2.5);
      canvas.drawPath(path, paintLinea);
    }

    canvas.restore();
  }

  void _dibujarTexto(Canvas canvas, String texto, double x, double y) {
    final textSpan = TextSpan(
      text: texto,
      style: TextStyle(
        color: colorTexto,
        fontSize: 10,
        fontWeight: FontWeight.w600,
        backgroundColor: const Color(0xDD222831),
      ),
    );
    final textPainter = TextPainter(
      text: textSpan,
      textDirection: TextDirection.ltr,
    )..layout();
    textPainter.paint(canvas, Offset(x - (textPainter.width / 2), y));
  }

  @override
  bool shouldRepaint(covariant RelacionesPainter oldDelegate) {
    return true;
  }
}
