import 'package:flutter/material.dart';

bool _sinAnimaciones(BuildContext context) => MediaQuery.maybeOf(context)?.disableAnimations ?? false;

/// Transición entre pantallas: aparece con un fundido y un leve desplazamiento hacia arriba.
Route<T> appRoute<T>(Widget page) {
  return PageRouteBuilder<T>(
    transitionDuration: const Duration(milliseconds: 380),
    reverseTransitionDuration: const Duration(milliseconds: 280),
    pageBuilder: (context, animation, secondaryAnimation) => page,
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      final curva = CurvedAnimation(parent: animation, curve: Curves.easeOutCubic);
      return FadeTransition(
        opacity: curva,
        child: SlideTransition(
          position: Tween(begin: const Offset(0, 0.05), end: Offset.zero).animate(curva),
          child: child,
        ),
      );
    },
  );
}

/// Entrada escalonada: cada elemento aparece un poco después del anterior.
class FadeSlideIn extends StatelessWidget {
  final Widget child;
  final int index;
  final double offset;

  const FadeSlideIn({super.key, required this.child, this.index = 0, this.offset = 22});

  @override
  Widget build(BuildContext context) {
    if (_sinAnimaciones(context)) return child;
    final retraso = index.clamp(0, 10) * 60;
    final total = 420 + retraso;
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: Duration(milliseconds: total),
      curve: Interval(retraso / total, 1, curve: Curves.easeOutCubic),
      child: child,
      builder: (context, t, child) => Opacity(
        opacity: t,
        child: Transform.translate(offset: Offset(0, (1 - t) * offset), child: child),
      ),
    );
  }
}

/// Número que "cuenta" hasta su valor.
class AnimatedCounter extends StatelessWidget {
  final int value;
  final TextStyle? style;

  const AnimatedCounter({super.key, required this.value, this.style});

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: value.toDouble()),
      duration: Duration(milliseconds: _sinAnimaciones(context) ? 0 : 900),
      curve: Curves.easeOutCubic,
      builder: (context, v, _) => Text(v.round().toString(), style: style),
    );
  }
}

/// Se "hunde" levemente al tocarlo.
class PressableScale extends StatefulWidget {
  final Widget child;
  const PressableScale({super.key, required this.child});

  @override
  State<PressableScale> createState() => _PressableScaleState();
}

class _PressableScaleState extends State<PressableScale> {
  bool _presionado = false;

  void _marcar(bool v) {
    if (_presionado != v) setState(() => _presionado = v);
  }

  @override
  Widget build(BuildContext context) {
    return Listener(
      onPointerDown: (_) => _marcar(true),
      onPointerUp: (_) => _marcar(false),
      onPointerCancel: (_) => _marcar(false),
      child: AnimatedScale(
        scale: _presionado ? 0.97 : 1,
        duration: const Duration(milliseconds: 140),
        curve: Curves.easeOut,
        child: widget.child,
      ),
    );
  }
}

/// Ícono que "respira" (para el encabezado y el splash).
class PulseIcon extends StatefulWidget {
  final IconData icon;
  final double size;
  final Color color;

  const PulseIcon({super.key, required this.icon, required this.color, this.size = 34});

  @override
  State<PulseIcon> createState() => _PulseIconState();
}

class _PulseIconState extends State<PulseIcon> with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 1800))..repeat(reverse: true);

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: Tween(begin: 0.92, end: 1.06).animate(CurvedAnimation(parent: _c, curve: Curves.easeInOut)),
      child: Icon(widget.icon, size: widget.size, color: widget.color),
    );
  }
}

/// Brillo que recorre los "esqueletos" mientras carga.
class Shimmer extends StatefulWidget {
  final Widget child;
  const Shimmer({super.key, required this.child});

  @override
  State<Shimmer> createState() => _ShimmerState();
}

class _ShimmerState extends State<Shimmer> with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 1300))..repeat();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final base = scheme.surfaceContainerHighest;
    final brillo = scheme.surface;
    return AnimatedBuilder(
      animation: _c,
      child: widget.child,
      builder: (context, child) => ShaderMask(
        blendMode: BlendMode.srcATop,
        shaderCallback: (rect) => LinearGradient(
          begin: Alignment(-1.5 + _c.value * 3, 0),
          end: Alignment(-0.5 + _c.value * 3, 0),
          colors: [base, brillo, base],
        ).createShader(rect),
        child: child,
      ),
    );
  }
}
