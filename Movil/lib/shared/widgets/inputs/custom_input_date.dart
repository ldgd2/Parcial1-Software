import 'package:flutter/material.dart';
import 'custom_input.dart';

class CustomDateInput extends StatefulWidget {
  final String hint;
  final String? label;
  final DateTime? initialDate;
  final Function(DateTime)? onDateSelected;
  final Color? fillColor;

  const CustomDateInput({
    super.key,
    required this.hint,
    this.label,
    this.initialDate,
    this.onDateSelected,
    this.fillColor,
  });

  @override
  State<CustomDateInput> createState() => _CustomDateInputState();
}

class _CustomDateInputState extends State<CustomDateInput> {
  final TextEditingController _controller = TextEditingController();
  DateTime? _selectedDate;

  @override
  void initState() {
    super.initState();
    if (widget.initialDate != null) {
      _selectedDate = widget.initialDate;
      _controller.text = _formatearFecha(widget.initialDate!);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  String _formatearFecha(DateTime fecha) {
    return "${fecha.day.toString().padLeft(2, '0')}/${fecha.month.toString().padLeft(2, '0')}/${fecha.year}";
  }

  Future<void> _seleccionarFecha(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate ?? DateTime.now(),
      firstDate: DateTime(1900),
      lastDate: DateTime(2100),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() {
        _selectedDate = picked;
        _controller.text = _formatearFecha(picked);
      });
      if (widget.onDateSelected != null) {
        widget.onDateSelected!(picked);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return CustomInput(
      controller: _controller,
      hint: widget.hint,
      label: widget.label,
      fillColor: widget.fillColor,
      readOnly: true,
      prefixIcon: Icons.calendar_today_outlined,
      onTap: () => _seleccionarFecha(context),
    );
  }
}
