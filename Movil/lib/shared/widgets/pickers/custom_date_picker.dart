import 'dart:ui';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_picker_field.dart';

enum DatePickerStyle {
  material,
  cupertinoWheel,
}

/// Selector de Fechas móvil (`CustomDatePicker`).
/// Soporta estilo Material (Calendario modal) y estilo Cupertino (Rueda giratoria iOS en BottomSheet).
class CustomDatePicker extends StatefulWidget {
  final String hint;
  final String? label;
  final DateTime? value;
  final DateTime? firstDate;
  final DateTime? lastDate;
  final ValueChanged<DateTime>? onDateSelected;
  final VoidCallback? onClear;
  final DatePickerStyle style;
  final Color? fillColor;
  final bool isDisabled;
  final String? errorText;
  final String Function(DateTime)? customFormatter;

  const CustomDatePicker({
    super.key,
    this.hint = "Seleccionar fecha",
    this.label,
    this.value,
    this.firstDate,
    this.lastDate,
    this.onDateSelected,
    this.onClear,
    this.style = DatePickerStyle.material,
    this.fillColor,
    this.isDisabled = false,
    this.errorText,
    this.customFormatter,
  });

  @override
  State<CustomDatePicker> createState() => _CustomDatePickerState();
}

class _CustomDatePickerState extends State<CustomDatePicker> {
  DateTime? _selectedDate;

  @override
  void initState() {
    super.initState();
    _selectedDate = widget.value;
  }

  @override
  void didUpdateWidget(covariant CustomDatePicker oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _selectedDate = widget.value;
    }
  }

  String _formatDate(DateTime date) {
    if (widget.customFormatter != null) {
      return widget.customFormatter!(date);
    }
    final dia = date.day.toString().padLeft(2, '0');
    final mes = date.month.toString().padLeft(2, '0');
    final anio = date.year.toString();
    return "$dia/$mes/$anio";
  }

  Future<void> _showPicker(BuildContext context) async {
    final effectiveFirst = widget.firstDate ?? DateTime(1900);
    final effectiveLast = widget.lastDate ?? DateTime(2100);
    final effectiveInitial = _selectedDate ?? DateTime.now();

    if (widget.style == DatePickerStyle.cupertinoWheel) {
      DateTime tempPickedDate = effectiveInitial;

      await showModalBottomSheet(
        context: context,
        backgroundColor: context.colores.fondoSecundario,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        builder: (ctx) {
          return SafeArea(
            child: SizedBox(
              height: 300,
              child: Column(
                children: [
                  // Barra de cabecera con acciones Cancelar y Listo
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        TextButton(
                          onPressed: () => Navigator.of(ctx).pop(),
                          child: Text(
                            "Cancelar",
                            style: TextStyle(color: context.colores.textoSecundario),
                          ),
                        ),
                        Text(
                          widget.label ?? "Seleccionar fecha",
                          style: context.textos.subtitulo.copyWith(fontSize: 16),
                        ),
                        TextButton(
                          onPressed: () {
                            setState(() => _selectedDate = tempPickedDate);
                            widget.onDateSelected?.call(tempPickedDate);
                            Navigator.of(ctx).pop();
                          },
                          child: Text(
                            "Listo",
                            style: TextStyle(
                              color: context.colores.primario,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Divider(height: 1),
                  Expanded(
                    child: ScrollConfiguration(
                      behavior: const CupertinoScrollBehavior().copyWith(
                        dragDevices: {
                          PointerDeviceKind.mouse,
                          PointerDeviceKind.touch,
                          PointerDeviceKind.stylus,
                          PointerDeviceKind.trackpad,
                        },
                      ),
                      child: CupertinoTheme(
                        data: CupertinoThemeData(
                          brightness: Theme.of(context).brightness,
                          textTheme: CupertinoTextThemeData(
                            dateTimePickerTextStyle: TextStyle(
                              color: context.colores.textoPrincipal,
                              fontSize: 20,
                            ),
                          ),
                        ),
                        child: CupertinoDatePicker(
                          mode: CupertinoDatePickerMode.date,
                          initialDateTime: effectiveInitial.isAfter(effectiveLast)
                              ? effectiveLast
                              : (effectiveInitial.isBefore(effectiveFirst)
                                  ? effectiveFirst
                                  : effectiveInitial),
                          minimumDate: effectiveFirst,
                          maximumDate: effectiveLast,
                          onDateTimeChanged: (newDate) {
                            tempPickedDate = newDate;
                          },
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      );
    } else {
      // Estilo Material Calendario
      final picked = await showDatePicker(
        context: context,
        initialDate: effectiveInitial.isAfter(effectiveLast)
            ? effectiveLast
            : (effectiveInitial.isBefore(effectiveFirst)
                ? effectiveFirst
                : effectiveInitial),
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
        setState(() => _selectedDate = picked);
        widget.onDateSelected?.call(picked);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return CustomPickerField(
      hint: widget.hint,
      label: widget.label,
      valueText: _selectedDate != null ? _formatDate(_selectedDate!) : null,
      prefixIcon: Icons.calendar_today_outlined,
      fillColor: widget.fillColor,
      isDisabled: widget.isDisabled,
      errorText: widget.errorText,
      onTap: () => _showPicker(context),
      onClear: widget.onClear != null
          ? () {
              setState(() => _selectedDate = null);
              widget.onClear!();
            }
          : null,
    );
  }
}
