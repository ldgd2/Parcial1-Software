import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_speed_dial_item.dart';

/// Menú Flotante Radial / Circular (`CustomRadialSpeedDial`):
/// Despliega los botones secundarios disparados en forma de abanico circular/radial
/// alrededor del botón principal flotante, con oscurecimiento de fondo (Backdrop).
class CustomRadialSpeedDial extends StatefulWidget {
  final List<CustomSpeedDialItem> items;
  final IconData openIcon;
  final IconData closeIcon;
  final double radius;
  final double startAngle;
  final double endAngle;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final Color? overlayColor;
  final double overlayOpacity;
  final double buttonSize;
  final double itemButtonSize;
  final bool enableHapticFeedback;

  const CustomRadialSpeedDial({
    super.key,
    required this.items,
    this.openIcon = Icons.auto_awesome_rounded,
    this.closeIcon = Icons.close_rounded,
    this.radius = 90.0,
    this.startAngle = math.pi, // 180° (Hacia la izquierda)
    this.endAngle = math.pi * 1.5, // 270° (Hacia arriba)
    this.backgroundColor,
    this.foregroundColor,
    this.overlayColor,
    this.overlayOpacity = 0.55,
    this.buttonSize = 56.0,
    this.itemButtonSize = 44.0,
    this.enableHapticFeedback = true,
  });

  @override
  State<CustomRadialSpeedDial> createState() => _CustomRadialSpeedDialState();
}

class _CustomRadialSpeedDialState extends State<CustomRadialSpeedDial> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _expandAnimation;
  late Animation<double> _rotationAnimation;
  OverlayEntry? _overlayEntry;
  final GlobalKey _fabKey = GlobalKey();

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 280),
    );
    _expandAnimation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutBack,
      reverseCurve: Curves.easeIn,
    );
    _rotationAnimation = Tween<double>(begin: 0.0, end: 0.5).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _removeOverlay();
    _controller.dispose();
    super.dispose();
  }

  bool get _isOpen => _overlayEntry != null;

  void _toggle() {
    if (widget.enableHapticFeedback) {
      HapticFeedback.lightImpact();
    }

    if (_isOpen) {
      _close();
    } else {
      _open();
    }
  }

  void _open() {
    if (_isOpen) return;

    final overlay = Overlay.of(context);
    final renderBox = _fabKey.currentContext?.findRenderObject() as RenderBox?;
    if (renderBox == null) return;

    final fabOffset = renderBox.localToGlobal(Offset.zero);
    final fabSize = renderBox.size;

    _overlayEntry = OverlayEntry(
      builder: (context) => _buildOverlayContent(fabOffset, fabSize),
    );

    overlay.insert(_overlayEntry!);
    _controller.forward();
    setState(() {});
  }

  void _close() {
    if (!_isOpen) return;

    _controller.reverse().then((_) {
      _removeOverlay();
      if (mounted) setState(() {});
    });
  }

  void _removeOverlay() {
    _overlayEntry?.remove();
    _overlayEntry = null;
  }

  Widget _buildOverlayContent(Offset fabOffset, Size fabSize) {
    final themeColores = context.colores;
    final totalItems = widget.items.length;
    final fabCenter = Offset(
      fabOffset.dx + (fabSize.width / 2),
      fabOffset.dy + (fabSize.height / 2),
    );

    return Material(
      color: Colors.transparent,
      child: Stack(
        children: [
          // 1. Backdrop Overlay oscuro
          Positioned.fill(
            child: GestureDetector(
              onTap: _close,
              behavior: HitTestBehavior.opaque,
              child: AnimatedBuilder(
                animation: _controller,
                builder: (context, child) {
                  return Container(
                    color: (widget.overlayColor ?? Colors.black)
                        .withValues(alpha: widget.overlayOpacity * _controller.value),
                  );
                },
              ),
            ),
          ),

          // 2. Botones secundarios desplegados en arco radial
          ...List.generate(totalItems, (index) {
            final item = widget.items[index];
            final itemBg = item.backgroundColor ?? themeColores.primario;
            final itemFg = item.foregroundColor ?? Colors.white;

            // Calcular ángulo de distribución
            final angleStep = totalItems > 1
                ? (widget.endAngle - widget.startAngle) / (totalItems - 1)
                : 0.0;
            final angle = widget.startAngle + (angleStep * index);

            return AnimatedBuilder(
              animation: _expandAnimation,
              builder: (context, child) {
                final currentRadius = widget.radius * _expandAnimation.value;
                final dx = fabCenter.dx + (currentRadius * math.cos(angle)) - (widget.itemButtonSize / 2);
                final dy = fabCenter.dy + (currentRadius * math.sin(angle)) - (widget.itemButtonSize / 2);

                return Positioned(
                  left: dx,
                  top: dy,
                  child: Transform.scale(
                    scale: _expandAnimation.value,
                    child: Opacity(
                      opacity: _controller.value,
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Material(
                            color: itemBg,
                            elevation: 5,
                            shadowColor: Colors.black.withValues(alpha: 0.3),
                            shape: const CircleBorder(),
                            child: InkWell(
                              onTap: () {
                                _close();
                                item.onPressed();
                              },
                              customBorder: const CircleBorder(),
                              child: Container(
                                width: widget.itemButtonSize,
                                height: widget.itemButtonSize,
                                alignment: Alignment.center,
                                child: Icon(
                                  item.icon,
                                  color: itemFg,
                                  size: item.iconSize,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            );
          }),

          // 3. Botón principal posicionado exactamente sobre el FAB original
          Positioned(
            left: fabOffset.dx,
            top: fabOffset.dy,
            child: _buildMainFab(context),
          ),
        ],
      ),
    );
  }

  Widget _buildMainFab(BuildContext context) {
    final themeColores = context.colores;
    final primaryBg = widget.backgroundColor ?? themeColores.primario;
    final primaryFg = widget.foregroundColor ?? Colors.white;

    return Material(
      color: primaryBg,
      elevation: 6,
      shadowColor: Colors.black.withValues(alpha: 0.3),
      shape: const CircleBorder(),
      child: InkWell(
        onTap: _toggle,
        customBorder: const CircleBorder(),
        child: Container(
          width: widget.buttonSize,
          height: widget.buttonSize,
          alignment: Alignment.center,
          child: RotationTransition(
            turns: _rotationAnimation,
            child: Icon(
              _isOpen ? widget.closeIcon : widget.openIcon,
              color: primaryFg,
              size: 28,
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Opacity(
      key: _fabKey,
      opacity: _isOpen ? 0.0 : 1.0,
      child: _buildMainFab(context),
    );
  }
}
