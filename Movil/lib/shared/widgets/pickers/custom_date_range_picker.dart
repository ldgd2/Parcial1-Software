import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_picker_field.dart';

/// Selector de Rango de Fechas móvil (`CustomDateRangePicker`).
/// Permite seleccionar fecha de inicio y fecha de fin (ej. para reservas, filtros, reportes).
class CustomDateRangePicker extends StatefulWidget {
  final String hint;
  final String? label;
  final DateTimeRange? value;
  final DateTime? firstDate;
  final DateTime? lastDate;
  final ValueChanged<DateTimeRange>? onRangeSelected;
  final VoidCallback? onClear;
  final Color? fillColor;
  final bool isDisabled;
  final String? errorText;

  const CustomDateRangePicker({
    super.key,
    this.hint = "Seleccionar rango de fechas",
    this.label,
    this.value,
    this.firstDate,
    this.lastDate,
    this.onRangeSelected,
    this.onClear,
    this.fillColor,
    this.isDisabled = false,
    this.errorText,
  });

  @override
  State<CustomDateRangePicker> createState() => _CustomDateRangePickerState();
}

class _CustomDateRangePickerState extends State<CustomDateRangePicker> {
  DateTimeRange? _selectedRange;

  @override
  void initState() {
    super.initState();
    _selectedRange = widget.value;
  }

  @override
  void didUpdateWidget(covariant CustomDateRangePicker oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _selectedRange = widget.value;
    }
  }

  String _formatSingleDate(DateTime date) {
    final dia = date.day.toString().padLeft(2, '0');
    final mes = date.month.toString().padLeft(2, '0');
    final anio = date.year.toString();
    return "$dia/$mes/$anio";
  }

  String _formatRange(DateTimeRange range) {
    return "${_formatSingleDate(range.start)}  →  ${_formatSingleDate(range.end)}";
  }

  Future<void> _showPicker(BuildContext context) async {
    final effectiveFirst = widget.firstDate ?? DateTime(2000);
    final effectiveLast = widget.lastDate ?? DateTime(2100);

    final picked = await showDateRangePicker(
      context: context,
      initialDateRange: _selectedRange,
      firstDate: effectiveFirst,
      lastDate: effectiveLast,
      builder: (ctx, child) {
        return Theme(
          data: Theme.of(ctx).copyWith(
            colorScheme: ColorScheme.light(
              primary: context.colores.primario,
              onPrimary: Colors.white,
              surface: context.colores.fondoSecundario,
              onSurface: context.colores.textoPrincipal,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      setState(() => _selectedRange = picked);
      widget.onRangeSelected?.call(picked);
    }
  }

  @override
  Widget build(BuildContext context) {
    return CustomPickerField(
      hint: widget.hint,
      label: widget.label,
      valueText: _selectedRange != null ? _formatRange(_selectedRange!) : null,
      prefixIcon: Icons.date_range_outlined,
      fillColor: widget.fillColor,
      isDisabled: widget.isDisabled,
      errorText: widget.errorText,
      onTap: () => _showPicker(context),
      onClear: widget.onClear != null
          ? () {
              setState(() => _selectedRange = null);
              widget.onClear!();
            }
          : null,
    );
  }
}
