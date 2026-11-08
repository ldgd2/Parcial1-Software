import 'dart:ui';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_picker_field.dart';

enum TimePickerStyle {
  materialClock,
  cupertinoWheel,
}

/// Selector de Hora móvil (`CustomTimePicker`).
/// Soporta estilo Material (Reloj interactivo analógico/digital) y estilo Cupertino (Rueda giratoria iOS).
class CustomTimePicker extends StatefulWidget {
  final String hint;
  final String? label;
  final TimeOfDay? value;
  final ValueChanged<TimeOfDay>? onTimeSelected;
  final VoidCallback? onClear;
  final TimePickerStyle style;
  final bool use24HourFormat;
  final Color? fillColor;
  final bool isDisabled;
  final String? errorText;

  const CustomTimePicker({
    super.key,
    this.hint = "Seleccionar hora",
    this.label,
    this.value,
    this.onTimeSelected,
    this.onClear,
    this.style = TimePickerStyle.materialClock,
    this.use24HourFormat = false,
    this.fillColor,
    this.isDisabled = false,
    this.errorText,
  });

  @override
  State<CustomTimePicker> createState() => _CustomTimePickerState();
}

class _CustomTimePickerState extends State<CustomTimePicker> {
  TimeOfDay? _selectedTime;

  @override
  void initState() {
    super.initState();
    _selectedTime = widget.value;
  }

  @override
  void didUpdateWidget(covariant CustomTimePicker oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _selectedTime = widget.value;
    }
  }

  String _formatTime(TimeOfDay time) {
    if (widget.use24HourFormat) {
      final hour = time.hour.toString().padLeft(2, '0');
      final minute = time.minute.toString().padLeft(2, '0');
      return "$hour:$minute";
    } else {
      final hour = time.hourOfPeriod == 0 ? 12 : time.hourOfPeriod;
      final minute = time.minute.toString().padLeft(2, '0');
      final period = time.period == DayPeriod.am ? "AM" : "PM";
      return "$hour:$minute $period";
    }
  }

  Future<void> _showPicker(BuildContext context) async {
    final effectiveInitial = _selectedTime ?? TimeOfDay.now();

    if (widget.style == TimePickerStyle.cupertinoWheel) {
      Duration tempDuration = Duration(
        hours: effectiveInitial.hour,
        minutes: effectiveInitial.minute,
      );

      await showModalBottomSheet(
        context: context,
        backgroundColor: context.colores.fondoSecundario,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        builder: (ctx) {
          return SafeArea(
            child: SizedBox(
              height: 280,
              child: Column(
                children: [
                  // Barra de cabecera con acciones
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
                          widget.label ?? "Seleccionar hora",
                          style: context.textos.subtitulo.copyWith(fontSize: 16),
                        ),
                        TextButton(
                          onPressed: () {
                            final chosenTime = TimeOfDay(
                              hour: tempDuration.inHours % 24,
                              minute: tempDuration.inMinutes % 60,
                            );
                            setState(() => _selectedTime = chosenTime);
                            widget.onTimeSelected?.call(chosenTime);
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
                              fontSize: 22,
                            ),
                          ),
                        ),
                        child: CupertinoTimerPicker(
                          mode: CupertinoTimerPickerMode.hm,
                          initialTimerDuration: tempDuration,
                          onTimerDurationChanged: (newDuration) {
                            tempDuration = newDuration;
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
      // Estilo Material Reloj Analógico
      final picked = await showTimePicker(
        context: context,
        initialTime: effectiveInitial,
        builder: (ctx, child) {
          return MediaQuery(
            data: MediaQuery.of(ctx).copyWith(
              alwaysUse24HourFormat: widget.use24HourFormat,
            ),
            child: Theme(
              data: Theme.of(ctx).copyWith(
                colorScheme: ColorScheme.light(
                  primary: context.colores.primario,
                  onPrimary: Colors.white,
                  surface: context.colores.fondoSecundario,
                  onSurface: context.colores.textoPrincipal,
                ),
              ),
              child: child!,
            ),
          );
        },
      );

      if (picked != null) {
        setState(() => _selectedTime = picked);
        widget.onTimeSelected?.call(picked);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return CustomPickerField(
      hint: widget.hint,
      label: widget.label,
      valueText: _selectedTime != null ? _formatTime(_selectedTime!) : null,
      prefixIcon: Icons.access_time_outlined,
      fillColor: widget.fillColor,
      isDisabled: widget.isDisabled,
      errorText: widget.errorText,
      onTap: () => _showPicker(context),
      onClear: widget.onClear != null
          ? () {
              setState(() => _selectedTime = null);
              widget.onClear!();
            }
          : null,
    );
  }
}
