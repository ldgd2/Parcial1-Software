import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_speed_dial_item.dart';

/// Menú Flotante Horizontal (`CustomHorizontalSpeedDial`):
/// Despliega los botones secundarios horizontalmente hacia la izquierda o derecha
/// con efecto de oscurecimiento de fondo (Backdrop Overlay) y animaciones fluidas.
class CustomHorizontalSpeedDial extends StatefulWidget {
  final List<CustomSpeedDialItem> items;
  final IconData openIcon;
  final IconData closeIcon;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final Color? overlayColor;
  final double overlayOpacity;
  final double spacing;
  final double buttonSize;
  final double itemButtonSize;
  final bool expandLeft;
  final bool enableHapticFeedback;

  const CustomHorizontalSpeedDial({
    super.key,
    required this.items,
    this.openIcon = Icons.more_horiz_rounded,
    this.closeIcon = Icons.close_rounded,
    this.backgroundColor,
    this.foregroundColor,
    this.overlayColor,
    this.overlayOpacity = 0.55,
    this.spacing = 10.0,
    this.buttonSize = 56.0,
    this.itemButtonSize = 44.0,
    this.expandLeft = true,
    this.enableHapticFeedback = true,
  });

  @override
  State<CustomHorizontalSpeedDial> createState() => _CustomHorizontalSpeedDialState();
}

class _CustomHorizontalSpeedDialState extends State<CustomHorizontalSpeedDial> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _rotationAnimation;
  OverlayEntry? _overlayEntry;
  final GlobalKey _fabKey = GlobalKey();

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 260),
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
    final mediaQuery = MediaQuery.of(context);

    final bottomPosition = mediaQuery.size.height - (fabOffset.dy + fabSize.height);
    final rightPosition = mediaQuery.size.width - (fabOffset.dx + fabSize.width);

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

          // 2. Fila horizontal de botones
          Positioned(
            bottom: bottomPosition,
            right: rightPosition,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                if (widget.expandLeft) ...[
                  ...List.generate(widget.items.length, (index) {
                    final item = widget.items[index];
                    final itemBg = item.backgroundColor ?? themeColores.primario;
                    final itemFg = item.foregroundColor ?? Colors.white;

                    final itemProgress = CurvedAnimation(
                      parent: _controller,
                      curve: Interval(
                        ((widget.items.length - 1 - index) / widget.items.length) * 0.4,
                        1.0,
                        curve: Curves.easeOutBack,
                      ),
                    );

                    return ScaleTransition(
                      scale: itemProgress,
                      child: FadeTransition(
                        opacity: _controller,
                        child: Padding(
                          padding: EdgeInsets.only(right: widget.spacing),
                          child: Material(
                            color: itemBg,
                            elevation: 4,
                            shadowColor: Colors.black.withValues(alpha: 0.25),
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
                        ),
                      ),
                    );
                  }),
                ],

                // Botón principal
                _buildMainFab(context),
              ],
            ),
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
