import 'package:flutter/material.dart';

import '../../core/utils/fmt.dart';

/// Avatar circular con las iniciales del registro (con Hero para la pantalla de detalle).
class EntityAvatar extends StatelessWidget {
  final String text;
  final Color color;
  final double size;
  final Object? heroTag;

  const EntityAvatar({super.key, required this.text, required this.color, this.size = 48, this.heroTag});

  @override
  Widget build(BuildContext context) {
    final avatar = Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [color, Color.lerp(color, Colors.black, 0.25)!],
        ),
        boxShadow: [BoxShadow(color: color.withAlpha(70), blurRadius: 12, offset: const Offset(0, 4))],
      ),
      alignment: Alignment.center,
      child: Text(
        Fmt.iniciales(text),
        style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: size * 0.36),
      ),
    );
    if (heroTag == null) return avatar;
    return Hero(tag: heroTag!, child: Material(type: MaterialType.transparency, child: avatar));
  }
}

/// Dato destacado en forma de "chip" (precio, estado, fecha…).
class InfoChip extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color? color;

  const InfoChip({super.key, required this.label, required this.icon, this.color});

  @override
  Widget build(BuildContext context) {
    final c = color ?? Theme.of(context).colorScheme.primary;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: c.withAlpha(28), borderRadius: BorderRadius.circular(20)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: c),
          const SizedBox(width: 4),
          Flexible(
            child: Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: c),
            ),
          ),
        ],
      ),
    );
  }
}

/// Burbuja de ícono con el color del módulo.
class IconBubble extends StatelessWidget {
  final IconData icon;
  final Color color;
  final double size;

  const IconBubble({super.key, required this.icon, required this.color, this.size = 44});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(color: color.withAlpha(32), borderRadius: BorderRadius.circular(size * 0.32)),
      child: Icon(icon, color: color, size: size * 0.52),
    );
  }
}
