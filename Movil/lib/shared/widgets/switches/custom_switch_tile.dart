import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_switch.dart';

/// Fila de Switch (`CustomSwitchTile`):
/// Elemento estándar de lista/configuración donde toda la fila es táctil para alternar el switch.
/// Mantiene estado interno para responder instantáneamente al toque en cualquier parte de la fila.
class CustomSwitchTile extends StatefulWidget {
  final String title;
  final String? subtitle;
  final bool value;
  final ValueChanged<bool>? onChanged;
  final IconData? leadingIcon;
  final Widget? leadingWidget;
  final Color? activeColor;
  final bool isDisabled;
  final bool isLoading;
  final bool hasBackground;
  final bool hasBorder;
  final Color? backgroundColor;
  final double borderRadius;
  final EdgeInsetsGeometry padding;

  const CustomSwitchTile({
    super.key,
    required this.title,
    required this.value,
    required this.onChanged,
    this.subtitle,
    this.leadingIcon,
    this.leadingWidget,
    this.activeColor,
    this.isDisabled = false,
    this.isLoading = false,
    this.hasBackground = false,
    this.hasBorder = false,
    this.backgroundColor,
    this.borderRadius = 12.0,
    this.padding = const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
  });

  @override
  State<CustomSwitchTile> createState() => _CustomSwitchTileState();
}

class _CustomSwitchTileState extends State<CustomSwitchTile> {
  late bool _currentValue;

  @override
  void initState() {
    super.initState();
    _currentValue = widget.value;
  }

  @override
  void didUpdateWidget(covariant CustomSwitchTile oldWidget) {
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
    final themeTextos = context.textos;
    final bool activo = !widget.isDisabled && !widget.isLoading && widget.onChanged != null;

    final resolvedBg = widget.hasBackground
        ? (widget.backgroundColor ?? themeColores.fondoSecundario)
        : Colors.transparent;

    return Material(
      color: resolvedBg,
      borderRadius: BorderRadius.circular(widget.borderRadius),
      child: InkWell(
        onTap: activo ? () => _handleToggle(!_currentValue) : null,
        borderRadius: BorderRadius.circular(widget.borderRadius),
        child: Container(
          padding: widget.padding,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(widget.borderRadius),
            border: widget.hasBorder
                ? Border.all(color: themeColores.borde.withValues(alpha: 0.5))
                : null,
          ),
          child: Row(
            children: [
              if (widget.leadingWidget != null) ...[
                widget.leadingWidget!,
                const SizedBox(width: 14),
              ] else if (widget.leadingIcon != null) ...[
                Icon(
                  widget.leadingIcon,
                  color: _currentValue ? (widget.activeColor ?? themeColores.primario) : themeColores.textoSecundario,
                  size: 24,
                ),
                const SizedBox(width: 14),
              ],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      widget.title,
                      style: themeTextos.cuerpo.copyWith(
                        fontWeight: FontWeight.w600,
                        color: widget.isDisabled
                            ? themeColores.textoSecundario.withValues(alpha: 0.6)
                            : themeColores.textoPrincipal,
                      ),
                    ),
                    if (widget.subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        widget.subtitle!,
                        style: themeTextos.cuerpoPequeno.copyWith(
                          color: themeColores.textoSecundario,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 12),
              CustomSwitch(
                value: _currentValue,
                onChanged: activo ? _handleToggle : null,
                activeColor: widget.activeColor,
                isDisabled: widget.isDisabled,
                isLoading: widget.isLoading,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
