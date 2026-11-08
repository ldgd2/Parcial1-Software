import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_slider.dart';

/// Tarjeta Deslizable (`CustomSliderCard`):
/// Contenedor estilizado tipo tarjeta para ajustes continuos en paneles de control o formularios modernos.
/// Mantiene estado interno para actualización en tiempo real de su insignia y barra de progreso.
class CustomSliderCard extends StatefulWidget {
  final String title;
  final String? description;
  final double value;
  final ValueChanged<double>? onChanged;
  final double min;
  final double max;
  final int? divisions;
  final IconData? icon;
  final Color? activeColor;
  final Color? backgroundColor;
  final String Function(double)? valueFormatter;
  final bool isDisabled;
  final double borderRadius;

  const CustomSliderCard({
    super.key,
    required this.title,
    required this.value,
    required this.onChanged,
    this.description,
    this.min = 0.0,
    this.max = 100.0,
    this.divisions,
    this.icon,
    this.activeColor,
    this.backgroundColor,
    this.valueFormatter,
    this.isDisabled = false,
    this.borderRadius = 16.0,
  });

  @override
  State<CustomSliderCard> createState() => _CustomSliderCardState();
}

class _CustomSliderCardState extends State<CustomSliderCard> {
  late double _currentValue;

  @override
  void initState() {
    super.initState();
    _currentValue = widget.value.clamp(widget.min, widget.max);
  }

  @override
  void didUpdateWidget(covariant CustomSliderCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _currentValue = widget.value.clamp(widget.min, widget.max);
    }
  }

  String _formatValue(double val) {
    if (widget.valueFormatter != null) {
      return widget.valueFormatter!(val);
    }
    return "${val.toInt()}%";
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    final resolvedActiveColor = widget.activeColor ?? themeColores.primario;
    final cardBg = widget.backgroundColor ?? themeColores.fondoSecundario;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(widget.borderRadius),
        border: Border.all(
          color: themeColores.borde.withValues(alpha: 0.6),
          width: 1.0,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              if (widget.icon != null) ...[
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: resolvedActiveColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    widget.icon,
                    color: resolvedActiveColor,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
              ],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
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
                      const SizedBox(height: 2),
                      Text(
                        widget.description!,
                        style: themeTextos.cuerpoPequeno.copyWith(
                          color: themeColores.textoSecundario,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: resolvedActiveColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _formatValue(_currentValue),
                  style: themeTextos.cuerpoPequeno.copyWith(
                    color: resolvedActiveColor,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          CustomSlider(
            value: _currentValue,
            min: widget.min,
            max: widget.max,
            divisions: widget.divisions,
            onChanged: widget.isDisabled
                ? null
                : (newVal) {
                    setState(() => _currentValue = newVal);
                    widget.onChanged?.call(newVal);
                  },
            activeColor: resolvedActiveColor,
            isDisabled: widget.isDisabled,
          ),
        ],
      ),
    );
  }
}
