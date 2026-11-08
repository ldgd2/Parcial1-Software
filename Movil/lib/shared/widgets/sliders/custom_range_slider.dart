import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Slider de Rango Doble (`CustomRangeSlider`):
/// Permite seleccionar un intervalo entre dos valores (mínimo y máximo).
/// Ideal para filtros de precio, edad, distancia o presupuestos.
/// Mantiene estado interno para actualización en tiempo real durante el arrastre.
class CustomRangeSlider extends StatefulWidget {
  final RangeValues values;
  final ValueChanged<RangeValues>? onChanged;
  final ValueChanged<RangeValues>? onChangeEnd;
  final double min;
  final double max;
  final int? divisions;
  final String? headerTitle;
  final String Function(RangeValues)? valueFormatter;
  final bool showValueIndicator;
  final Color? activeColor;
  final Color? inactiveColor;
  final bool isDisabled;
  final double trackHeight;

  const CustomRangeSlider({
    super.key,
    required this.values,
    required this.onChanged,
    this.onChangeEnd,
    this.min = 0.0,
    this.max = 100.0,
    this.divisions,
    this.headerTitle,
    this.valueFormatter,
    this.showValueIndicator = true,
    this.activeColor,
    this.inactiveColor,
    this.isDisabled = false,
    this.trackHeight = 6.0,
  });

  @override
  State<CustomRangeSlider> createState() => _CustomRangeSliderState();
}

class _CustomRangeSliderState extends State<CustomRangeSlider> {
  late RangeValues _currentValues;

  @override
  void initState() {
    super.initState();
    _currentValues = _clampValues(widget.values);
  }

  @override
  void didUpdateWidget(covariant CustomRangeSlider oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.values != widget.values) {
      _currentValues = _clampValues(widget.values);
    }
  }

  RangeValues _clampValues(RangeValues vals) {
    final start = vals.start.clamp(widget.min, widget.max);
    final end = vals.end.clamp(start, widget.max);
    return RangeValues(start, end);
  }

  String _formatSingleValue(double val) {
    return val.toStringAsFixed(val.truncateToDouble() == val ? 0 : 1);
  }

  String _formatRange(RangeValues range) {
    if (widget.valueFormatter != null) {
      return widget.valueFormatter!(range);
    }
    return "${_formatSingleValue(range.start)} - ${_formatSingleValue(range.end)}";
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;
    final bool activo = !widget.isDisabled && widget.onChanged != null;

    final resolvedActiveColor = widget.activeColor ?? themeColores.primario;
    final resolvedInactiveColor = widget.inactiveColor ?? themeColores.borde;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
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
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: resolvedActiveColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    _formatRange(_currentValues),
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
        SliderTheme(
          data: SliderTheme.of(context).copyWith(
            trackHeight: widget.trackHeight,
            activeTrackColor: resolvedActiveColor,
            inactiveTrackColor: resolvedInactiveColor,
            thumbColor: resolvedActiveColor,
            overlayColor: resolvedActiveColor.withValues(alpha: 0.16),
            rangeThumbShape: const RoundRangeSliderThumbShape(enabledThumbRadius: 10.0),
            rangeValueIndicatorShape: const PaddleRangeSliderValueIndicatorShape(),
            valueIndicatorColor: resolvedActiveColor,
            valueIndicatorTextStyle: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          child: RangeSlider(
            values: _currentValues,
            min: widget.min,
            max: widget.max,
            divisions: widget.divisions,
            labels: RangeLabels(
              _formatSingleValue(_currentValues.start),
              _formatSingleValue(_currentValues.end),
            ),
            onChanged: activo
                ? (newVals) {
                    setState(() => _currentValues = newVals);
                    widget.onChanged?.call(newVals);
                  }
                : null,
            onChangeEnd: widget.onChangeEnd,
          ),
        ),
      ],
    );
  }
}
