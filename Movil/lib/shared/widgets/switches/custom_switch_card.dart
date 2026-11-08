import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_switch.dart';

/// Tarjeta con Interruptor (`CustomSwitchCard`):
/// Ideal para pantallas de ajustes, paneles de control o activación de módulos/funciones destacadas.
/// Mantiene estado interno reactivo para alternar el borde coloreado, el icono y el interruptor al pulsar.
class CustomSwitchCard extends StatefulWidget {
  final String title;
  final String? description;
  final bool value;
  final ValueChanged<bool>? onChanged;
  final IconData? icon;
  final Color? activeColor;
  final Color? iconColor;
  final Color? backgroundColor;
  final bool isDisabled;
  final bool isLoading;
  final double borderRadius;

  const CustomSwitchCard({
    super.key,
    required this.title,
    required this.value,
    required this.onChanged,
    this.description,
    this.icon,
    this.activeColor,
    this.iconColor,
    this.backgroundColor,
    this.isDisabled = false,
    this.isLoading = false,
    this.borderRadius = 16.0,
  });

  @override
  State<CustomSwitchCard> createState() => _CustomSwitchCardState();
}

class _CustomSwitchCardState extends State<CustomSwitchCard> {
  late bool _currentValue;

  @override
  void initState() {
    super.initState();
    _currentValue = widget.value;
  }

  @override
  void didUpdateWidget(covariant CustomSwitchCard oldWidget) {
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

    final resolvedActiveColor = widget.activeColor ?? themeColores.primario;
    final cardBg = widget.backgroundColor ?? themeColores.fondoSecundario;

    return Material(
      color: cardBg,
      borderRadius: BorderRadius.circular(widget.borderRadius),
      child: InkWell(
        onTap: activo ? () => _handleToggle(!_currentValue) : null,
        borderRadius: BorderRadius.circular(widget.borderRadius),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(widget.borderRadius),
            border: Border.all(
              color: _currentValue
                  ? resolvedActiveColor.withValues(alpha: 0.35)
                  : themeColores.borde.withValues(alpha: 0.5),
              width: _currentValue ? 1.5 : 1.0,
            ),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              if (widget.icon != null) ...[
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: _currentValue
                        ? resolvedActiveColor.withValues(alpha: 0.12)
                        : themeColores.borde.withValues(alpha: 0.3),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    widget.icon,
                    color: _currentValue
                        ? resolvedActiveColor
                        : (widget.iconColor ?? themeColores.textoSecundario),
                    size: 22,
                  ),
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
                        fontWeight: FontWeight.bold,
                        color: widget.isDisabled
                            ? themeColores.textoSecundario.withValues(alpha: 0.6)
                            : themeColores.textoPrincipal,
                      ),
                    ),
                    if (widget.description != null) ...[
                      const SizedBox(height: 3),
                      Text(
                        widget.description!,
                        style: themeTextos.cuerpoPequeno.copyWith(
                          color: themeColores.textoSecundario,
                          fontSize: 13,
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
                activeColor: resolvedActiveColor,
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
