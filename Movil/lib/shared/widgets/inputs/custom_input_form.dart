import 'package:flutter/material.dart';
import 'custom_input.dart';

/// Campo de Formulario con Validación Avanzada (`CustomFormFieldInput`):
/// Proporciona validaciones rápidas preconfiguradas (requerido, longitud mínima, regex personalizada)
/// y retroalimentación visual inmediata con mensajes de error.
class CustomFormFieldInput extends StatelessWidget {
  final String label;
  final String hint;
  final String? helperText;
  final bool isRequired;
  final int? minLength;
  final String? Function(String?)? customValidator;
  final ValueChanged<String>? onChanged;
  final TextEditingController? controller;
  final IconData? prefixIcon;
  final TextInputType keyboardType;
  final Color? fillColor;

  const CustomFormFieldInput({
    super.key,
    required this.label,
    required this.hint,
    this.helperText,
    this.isRequired = false,
    this.minLength,
    this.customValidator,
    this.onChanged,
    this.controller,
    this.prefixIcon,
    this.keyboardType = TextInputType.text,
    this.fillColor,
  });

  String? _validate(String? val) {
    if (isRequired && (val == null || val.trim().isEmpty)) {
      return "Este campo es obligatorio";
    }
    if (minLength != null && val != null && val.trim().length < minLength!) {
      return "Debe contener al menos $minLength caracteres";
    }
    if (customValidator != null) {
      return customValidator!(val);
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return CustomInput(
      label: label,
      hint: hint,
      helperText: helperText,
      prefixIcon: prefixIcon,
      keyboardType: keyboardType,
      controller: controller,
      fillColor: fillColor,
      validator: _validate,
      onChanged: onChanged,
    );
  }
}
