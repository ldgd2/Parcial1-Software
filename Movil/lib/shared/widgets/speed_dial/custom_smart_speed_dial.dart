import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_speed_dial_item.dart';

/// Menú Flotante Inteligente (`CustomSmartSpeedDial`):
/// Detecta automáticamente su posición en la pantalla (usando renderBox offset)
/// y decide qué tipo de animación y distribución de botones utilizar:
/// - Esquinas: Despliegue en abanico (90°).
/// - Lados (Centro-Izquierda/Centro-Derecha): Despliegue Vertical.
/// - Medio (Abajo/Arriba): Semicírculo (180°).
/// - Centro Absoluto: Círculo completo (360°).
class CustomSmartSpeedDial extends StatefulWidget {
  final List<CustomSpeedDialItem> items;
  final IconData openIcon;
  final IconData closeIcon;
  final double radius;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final Color? overlayColor;
  final double overlayOpacity;
  final double buttonSize;
  final double itemButtonSize;
  final bool enableHapticFeedback;

  const CustomSmartSpeedDial({
    super.key,
    required this.items,
    this.openIcon = Icons.add_rounded,
    this.closeIcon = Icons.close_rounded,
    this.radius = 115.0,
    this.backgroundColor,
    this.foregroundColor,
    this.overlayColor,
    this.overlayOpacity = 0.55,
    this.buttonSize = 56.0,
    this.itemButtonSize = 44.0,
    this.enableHapticFeedback = true,
  });

  @override
  State<CustomSmartSpeedDial> createState() => _CustomSmartSpeedDialState();
}

class _CustomSmartSpeedDialState extends State<CustomSmartSpeedDial> with SingleTickerProviderStateMixin {
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
    final screenSize = MediaQuery.of(context).size;

    _overlayEntry = OverlayEntry(
      builder: (context) => _buildOverlayContent(fabOffset, fabSize, screenSize),
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

  // --- Lógica de Detección de Posición ---
  // Clasifica la posición del botón en la pantalla.
  _SpeedDialLayout _determineLayout(Offset center, Size screenSize) {
    final double dx = center.dx;
    final double dy = center.dy;
    final double w = screenSize.width;
    final double h = screenSize.height;

    final bool isLeft = dx < w * 0.35;
    final bool isRight = dx > w * 0.65;
    final bool isTop = dy < h * 0.35;
    final bool isBottom = dy > h * 0.65;
    final bool isCenterX = !isLeft && !isRight;
    final bool isCenterY = !isTop && !isBottom;

    if (isCenterX && isCenterY) return _SpeedDialLayout.fullCircle;
    
    if (isCenterX) {
      return isTop ? _SpeedDialLayout.halfCircleDown : _SpeedDialLayout.halfCircleUp;
    }

    if (isCenterY) {
      return isLeft ? _SpeedDialLayout.halfCircleRight : _SpeedDialLayout.halfCircleLeft;
    }

    // Esquinas
    if (isTop && isLeft) return _SpeedDialLayout.fanBottomRight;
    if (isTop && isRight) return _SpeedDialLayout.fanBottomLeft;
    if (isBottom && isLeft) return _SpeedDialLayout.fanTopRight;
    if (isBottom && isRight) return _SpeedDialLayout.fanTopLeft;

    return _SpeedDialLayout.halfCircleUp; // Fallback
  }

  Widget _buildOverlayContent(Offset fabOffset, Size fabSize, Size screenSize) {
    final themeColores = context.colores;
    final totalItems = widget.items.length;
    final fabCenter = Offset(
      fabOffset.dx + (fabSize.width / 2),
      fabOffset.dy + (fabSize.height / 2),
    );

    final layout = _determineLayout(fabCenter, screenSize);

    return Material(
      color: Colors.transparent,
      child: Stack(
        children: [
          // 1. Backdrop
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

          // 2. Botones secundarios
          ...List.generate(totalItems, (index) {
            final item = widget.items[index];
            final itemBg = item.backgroundColor ?? themeColores.primario;
            final itemFg = item.foregroundColor ?? Colors.white;

            final themeTextos = context.textos;

            return AnimatedBuilder(
              animation: _expandAnimation,
              builder: (context, child) {
                final double currentVal = _expandAnimation.value;
                _ItemPositionData posData = _calculateItemPosition(layout, index, totalItems, fabCenter, currentVal);
                Offset pos = posData.pos;
                double angle = posData.angle;
                
                final labelPos = _getLabelPosition(layout, angle);

                final dx = pos.dx - (widget.itemButtonSize / 2);
                final dy = pos.dy - (widget.itemButtonSize / 2);

                final labelBg = item.labelBackgroundColor ?? themeColores.fondoSecundario;
                final labelFg = item.labelTextColor ?? themeColores.textoPrincipal;

                Widget labelWidget = Material(
                  color: labelBg,
                  elevation: 3,
                  shadowColor: Colors.black.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    child: Text(
                      item.label,
                      textAlign: TextAlign.center,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: themeTextos.cuerpoPequeno.copyWith(
                        color: labelFg,
                        fontWeight: FontWeight.bold,
                        fontSize: 11.5,
                      ),
                    ),
                  ),
                );

                Widget labelContainer = Positioned(
                  top: labelPos == _LabelPosition.bottom ? widget.itemButtonSize + 6 : (labelPos == _LabelPosition.left || labelPos == _LabelPosition.right ? -20 : null),
                  bottom: labelPos == _LabelPosition.top ? widget.itemButtonSize + 6 : (labelPos == _LabelPosition.left || labelPos == _LabelPosition.right ? -20 : null),
                  left: labelPos == _LabelPosition.right ? widget.itemButtonSize + 8 : (labelPos == _LabelPosition.top || labelPos == _LabelPosition.bottom ? -60 : null),
                  right: labelPos == _LabelPosition.left ? widget.itemButtonSize + 8 : (labelPos == _LabelPosition.top || labelPos == _LabelPosition.bottom ? -60 : null),
                  child: Center(
                    child: SizedBox(
                      width: 120,
                      child: Align(
                        alignment: labelPos == _LabelPosition.left 
                            ? Alignment.centerRight 
                            : (labelPos == _LabelPosition.right 
                                ? Alignment.centerLeft 
                                : Alignment.center),
                        child: labelWidget,
                      )
                    )
                  ),
                );

                return Positioned(
                  left: dx,
                  top: dy,
                  child: Transform.scale(
                    scale: _expandAnimation.value,
                    child: Opacity(
                      opacity: _controller.value,
                      child: Stack(
                        clipBehavior: Clip.none,
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
                          labelContainer,
                        ],
                      ),
                    ),
                  ),
                );
              },
            );
          }),

          // 3. Main FAB
          Positioned(
            left: fabOffset.dx,
            top: fabOffset.dy,
            child: _buildMainFab(context),
          ),
        ],
      ),
    );
  }

  _ItemPositionData _calculateItemPosition(_SpeedDialLayout layout, int index, int totalItems, Offset center, double animValue) {
    // Espaciado para listas verticales
    const double verticalSpacing = 16.0;
    
    // Casos Radiales/Abanico
    double startAngle = 0;
    double endAngle = 0;

    switch (layout) {
      case _SpeedDialLayout.fullCircle:
        startAngle = 0;
        endAngle = 2 * math.pi;
        break;
      case _SpeedDialLayout.halfCircleUp:
        startAngle = math.pi;
        endAngle = 2 * math.pi;
        break;
      case _SpeedDialLayout.halfCircleDown:
        startAngle = 0;
        endAngle = math.pi;
        break;
      case _SpeedDialLayout.halfCircleRight:
        startAngle = -math.pi * 0.5;
        endAngle = math.pi * 0.5;
        break;
      case _SpeedDialLayout.halfCircleLeft:
        startAngle = math.pi * 0.5;
        endAngle = math.pi * 1.5;
        break;
      case _SpeedDialLayout.fanTopLeft: // Esquina Inferior Derecha -> Abanico Arriba-Izquierda
        startAngle = math.pi;
        endAngle = math.pi * 1.5;
        break;
      case _SpeedDialLayout.fanTopRight: // Esquina Inferior Izquierda -> Abanico Arriba-Derecha
        startAngle = math.pi * 1.5;
        endAngle = math.pi * 2;
        break;
      case _SpeedDialLayout.fanBottomLeft: // Esquina Superior Derecha -> Abanico Abajo-Izquierda
        startAngle = math.pi * 0.5;
        endAngle = math.pi;
        break;
      case _SpeedDialLayout.fanBottomRight: // Esquina Superior Izquierda -> Abanico Abajo-Derecha
        startAngle = 0;
        endAngle = math.pi * 0.5;
        break;
      default:
        startAngle = math.pi;
        endAngle = math.pi * 2;
    }

    // Distribuir el ángulo
    // Si es fullCircle, dividimos entre totalItems.
    // Si no es fullCircle, dividimos entre (totalItems - 1).
    double angleStep;
    if (layout == _SpeedDialLayout.fullCircle) {
      angleStep = (endAngle - startAngle) / totalItems;
    } else {
      angleStep = totalItems > 1 ? (endAngle - startAngle) / (totalItems - 1) : 0.0;
    }

    final double angle = startAngle + (angleStep * index);
    final double currentRadius = widget.radius * animValue;

    return _ItemPositionData(
      Offset(
        center.dx + (currentRadius * math.cos(angle)),
        center.dy + (currentRadius * math.sin(angle)),
      ),
      angle,
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

enum _SpeedDialLayout {
  fullCircle,
  halfCircleUp,
  halfCircleDown,
  halfCircleRight,
  halfCircleLeft,
  fanTopLeft,
  fanTopRight,
  fanBottomLeft,
  fanBottomRight,
}

enum _LabelPosition { top, bottom, left, right }

_LabelPosition _getLabelPosition(_SpeedDialLayout layout, double angle) {
  final double c = math.cos(angle);
  final double s = math.sin(angle);
  
  if (c < -0.35) {
    return _LabelPosition.left;
  } else if (c > 0.35) {
    return _LabelPosition.right;
  } else {
    return s < 0 ? _LabelPosition.top : _LabelPosition.bottom;
  }
}

class _ItemPositionData {
  final Offset pos;
  final double angle;
  _ItemPositionData(this.pos, this.angle);
}
