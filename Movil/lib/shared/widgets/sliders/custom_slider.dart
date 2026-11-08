import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Slider base del cual heredarán las abstracciones y variantes de barras deslizables.
/// Controla valores continuos o discretos, temas, etiquetas de valor, iconos y estados.
/// Mantiene estado interno para permitir arrastre fluido (smooth drag) en tiempo real.
class CustomSlider extends StatefulWidget {
  final double value;
  final ValueChanged<double>? onChanged;
  final ValueChanged<double>? onChangeEnd;
  final double min;
  final double max;
  final int? divisions;
  final String? headerTitle;
  final String? label;
  final String Function(double)? valueFormatter;
  final bool showValueIndicator;
  final IconData? prefixIcon;
  final IconData? suffixIcon;
  final Color? activeColor;
  final Color? inactiveColor;
  final Color? thumbColor;
  final bool isDisabled;
  final double trackHeight;

  const CustomSlider({
    super.key,
    required this.value,
    required this.onChanged,
    this.onChangeEnd,
    this.min = 0.0,
    this.max = 100.0,
    this.divisions,
    this.headerTitle,
    this.label,
    this.valueFormatter,
    this.showValueIndicator = false,
    this.prefixIcon,
    this.suffixIcon,
    this.activeColor,
    this.inactiveColor,
    this.thumbColor,
    this.isDisabled = false,
    this.trackHeight = 6.0,
  });

  @override
  State<CustomSlider> createState() => _CustomSliderState();
}

class _CustomSliderState extends State<CustomSlider> {
  late double _currentValue;

  @override
  void initState() {
    super.initState();
    _currentValue = widget.value.clamp(widget.min, widget.max);
  }

  @override
  void didUpdateWidget(covariant CustomSlider oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _currentValue = widget.value.clamp(widget.min, widget.max);
    }
  }

  String _formatValue(double val) {
    if (widget.valueFormatter != null) {
      return widget.valueFormatter!(val);
    }
    return val.toStringAsFixed(val.truncateToDouble() == val ? 0 : 1);
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;
    final bool activo = !widget.isDisabled && widget.onChanged != null;

    final resolvedActiveColor = widget.activeColor ?? themeColores.primario;
    final resolvedInactiveColor = widget.inactiveColor ?? themeColores.borde;
    final resolvedThumbColor = widget.thumbColor ?? resolvedActiveColor;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // Cabecera opcional con Título y Valor actual
        if (widget.headerTitle != null || widget.showValueIndicator) ...[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              if (widget.headerTitle != null)
                Text(
                  widget.headerTitle!,
                  style: themeTextos.cuerpoPequeno.copyWith(
                    fontWeight: FontWeight.bold,
                    color: widget.isDisabled
                        ? themeColores.textoSecundario.withValues(alpha: 0.6)
                        : themeColores.textoPrincipal,
                  ),
                ),
              if (widget.showValueIndicator)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: resolvedActiveColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    _formatValue(_currentValue),
                    style: themeTextos.cuerpoPequeno.copyWith(
                      color: resolvedActiveColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 4),
        ],

        // Barra Deslizable con soporte para iconos
        Row(
          children: [
            if (widget.prefixIcon != null) ...[
              Icon(
                widget.prefixIcon,
                color: activo ? themeColores.textoSecundario : themeColores.textoSecundario.withValues(alpha: 0.5),
                size: 20,
              ),
              const SizedBox(width: 8),
            ],
            Expanded(
              child: SliderTheme(
                data: SliderTheme.of(context).copyWith(
                  trackHeight: widget.trackHeight,
                  activeTrackColor: resolvedActiveColor,
                  inactiveTrackColor: resolvedInactiveColor,
                  thumbColor: resolvedThumbColor,
                  overlayColor: resolvedActiveColor.withValues(alpha: 0.16),
                  thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 10.0),
                  overlayShape: const RoundSliderOverlayShape(overlayRadius: 20.0),
                  valueIndicatorShape: const PaddleSliderValueIndicatorShape(),
                  valueIndicatorColor: resolvedActiveColor,
                  valueIndicatorTextStyle: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
                child: Slider(
                  value: _currentValue,
                  min: widget.min,
                  max: widget.max,
                  divisions: widget.divisions,
                  label: widget.label ?? (widget.divisions != null ? _formatValue(_currentValue) : null),
                  onChanged: activo
                      ? (newVal) {
                          setState(() => _currentValue = newVal);
                          widget.onChanged?.call(newVal);
                        }
                      : null,
                  onChangeEnd: widget.onChangeEnd,
                ),
              ),
            ),
            if (widget.suffixIcon != null) ...[
              const SizedBox(width: 8),
              Icon(
                widget.suffixIcon,
                color: activo ? themeColores.textoSecundario : themeColores.textoSecundario.withValues(alpha: 0.5),
                size: 20,
              ),
            ],
          ],
        ),
      ],
    );
  }
}
