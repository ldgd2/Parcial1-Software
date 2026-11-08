import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Slider Discreto por Pasos (`CustomDiscreteSlider`):
/// Permite seleccionar entre pasos definidos con etiquetas visibles debajo de cada punto
/// (ej. Niveles: Bajo, Medio, Alto, Máximo o Calificaciones de 1 a 5).
/// Mantiene estado interno para responder en tiempo real al arrastre.
class CustomDiscreteSlider extends StatefulWidget {
  final int value;
  final List<String> steps;
  final ValueChanged<int>? onChanged;
  final String? headerTitle;
  final Color? activeColor;
  final bool isDisabled;

  const CustomDiscreteSlider({
    super.key,
    required this.value,
    required this.steps,
    required this.onChanged,
    this.headerTitle,
    this.activeColor,
    this.isDisabled = false,
  }) : assert(steps.length >= 2, "Debe haber al menos 2 pasos definidos");

  @override
  State<CustomDiscreteSlider> createState() => _CustomDiscreteSliderState();
}

class _CustomDiscreteSliderState extends State<CustomDiscreteSlider> {
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.value.clamp(0, widget.steps.length - 1);
  }

  @override
  void didUpdateWidget(covariant CustomDiscreteSlider oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _currentIndex = widget.value.clamp(0, widget.steps.length - 1);
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;
    final bool activo = !widget.isDisabled && widget.onChanged != null;

    final resolvedActiveColor = widget.activeColor ?? themeColores.primario;
    final clampedIndex = _currentIndex.clamp(0, widget.steps.length - 1);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (widget.headerTitle != null) ...[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                widget.headerTitle!,
                style: themeTextos.cuerpoPequeno.copyWith(
                  fontWeight: FontWeight.bold,
                  color: widget.isDisabled
                      ? themeColores.textoSecundario.withValues(alpha: 0.6)
                      : themeColores.textoPrincipal,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: resolvedActiveColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  widget.steps[clampedIndex],
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

        // Slider con divisiones
        SliderTheme(
          data: SliderTheme.of(context).copyWith(
            trackHeight: 6.0,
            activeTrackColor: resolvedActiveColor,
            inactiveTrackColor: themeColores.borde,
            thumbColor: resolvedActiveColor,
            overlayColor: resolvedActiveColor.withValues(alpha: 0.16),
            thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 10.0),
            tickMarkShape: const RoundSliderTickMarkShape(tickMarkRadius: 3.5),
            activeTickMarkColor: Colors.white,
            inactiveTickMarkColor: themeColores.textoSecundario.withValues(alpha: 0.4),
          ),
          child: Slider(
            value: clampedIndex.toDouble(),
            min: 0,
            max: (widget.steps.length - 1).toDouble(),
            divisions: widget.steps.length - 1,
            onChanged: activo
                ? (val) {
                    final newIdx = val.round();
                    setState(() => _currentIndex = newIdx);
                    widget.onChanged?.call(newIdx);
                  }
                : null,
          ),
        ),

        // Etiquetas debajo de los pasos
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(widget.steps.length, (index) {
              final isCurrent = index == clampedIndex;
              return Text(
                widget.steps[index],
                style: themeTextos.cuerpoPequeno.copyWith(
                  fontSize: 11,
                  fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
                  color: isCurrent
                      ? resolvedActiveColor
                      : themeColores.textoSecundario.withValues(alpha: 0.7),
                ),
              );
            }),
          ),
        ),
      ],
    );
  }
}
