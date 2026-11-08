import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Switch base del cual derivan los componentes y abstracciones de interruptores.
/// Proporciona un interruptor táctil animado, adaptable a iOS y Android,
/// con soporte para estados de carga (loading), deshabilitado, iconos internos y actualización reactiva inmediata.
class CustomSwitch extends StatefulWidget {
  final bool value;
  final ValueChanged<bool>? onChanged;
  final Color? activeColor;
  final Color? activeTrackColor;
  final Color? inactiveThumbColor;
  final Color? inactiveTrackColor;
  final bool isDisabled;
  final bool isLoading;
  final double scale;
  final IconData? activeIcon;
  final IconData? inactiveIcon;

  const CustomSwitch({
    super.key,
    required this.value,
    required this.onChanged,
    this.activeColor,
    this.activeTrackColor,
    this.inactiveThumbColor,
    this.inactiveTrackColor,
    this.isDisabled = false,
    this.isLoading = false,
    this.scale = 0.95,
    this.activeIcon,
    this.inactiveIcon,
  });

  @override
  State<CustomSwitch> createState() => _CustomSwitchState();
}

class _CustomSwitchState extends State<CustomSwitch> {
  late bool _currentValue;

  @override
  void initState() {
    super.initState();
    _currentValue = widget.value;
  }

  @override
  void didUpdateWidget(covariant CustomSwitch oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _currentValue = widget.value;
    }
  }

  void _handleToggle(bool newValue) {
    setState(() => _currentValue = newValue);
    widget.onChanged?.call(newValue);
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final bool activo = !widget.isDisabled && !widget.isLoading && widget.onChanged != null;

    final resolvedActiveColor = widget.activeColor ?? themeColores.primario;
    final resolvedInactiveThumb = widget.inactiveThumbColor ?? (widget.isDisabled ? themeColores.borde : Colors.white);
    final resolvedInactiveTrack = widget.inactiveTrackColor ?? themeColores.borde.withValues(alpha: 0.6);

    Widget switchWidget;

    if (widget.isLoading) {
      switchWidget = SizedBox(
        width: 38 * widget.scale,
        height: 24 * widget.scale,
        child: Center(
          child: SizedBox(
            width: 16 * widget.scale,
            height: 16 * widget.scale,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: resolvedActiveColor,
            ),
          ),
        ),
      );
    } else if (widget.activeIcon != null || widget.inactiveIcon != null) {
      // Switch con iconos en el Thumb (ej. Sol/Luna, Campana/Mute)
      switchWidget = GestureDetector(
        onTap: activo ? () => _handleToggle(!_currentValue) : null,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeInOut,
          width: 52 * widget.scale,
          height: 30 * widget.scale,
          padding: EdgeInsets.symmetric(horizontal: 3 * widget.scale),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20 * widget.scale),
            color: !activo
                ? themeColores.borde.withValues(alpha: 0.5)
                : (_currentValue ? resolvedActiveColor : resolvedInactiveTrack),
          ),
          child: AnimatedAlign(
            duration: const Duration(milliseconds: 220),
            curve: Curves.easeInOut,
            alignment: _currentValue ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              width: 24 * widget.scale,
              height: 24 * widget.scale,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.15),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Icon(
                _currentValue ? (widget.activeIcon ?? Icons.check) : (widget.inactiveIcon ?? Icons.close),
                size: 14 * widget.scale,
                color: _currentValue ? resolvedActiveColor : themeColores.textoSecundario,
              ),
            ),
          ),
        ),
      );
    } else {
      // Switch adaptable nativo
      switchWidget = Transform.scale(
        scale: widget.scale,
        child: CupertinoSwitch(
          value: _currentValue,
          activeTrackColor: resolvedActiveColor,
          thumbColor: _currentValue ? Colors.white : resolvedInactiveThumb,
          inactiveTrackColor: resolvedInactiveTrack,
          onChanged: activo ? _handleToggle : null,
        ),
      );
    }

    return Opacity(
      opacity: widget.isDisabled ? 0.5 : 1.0,
      child: switchWidget,
    );
  }
}
