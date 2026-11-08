import 'package:flutter/material.dart';
import 'custom_input.dart';

/// Campo de Correo Electrónico (`CustomEmailInput`):
/// Optimizado para el teclado móvil con tecla '@' y validador de formato de correo integrado.
class CustomEmailInput extends StatelessWidget {
  final String? label;
  final String hint;
  final ValueChanged<String>? onChanged;
  final TextEditingController? controller;
  final String? Function(String?)? customValidator;
  final Color? fillColor;
  final bool isRequired;

  const CustomEmailInput({
    super.key,
    this.label = "Correo Electrónico",
    this.hint = "ejemplo@correo.com",
    this.onChanged,
    this.controller,
    this.customValidator,
    this.fillColor,
    this.isRequired = true,
  });

  String? _defaultEmailValidator(String? value) {
    if (isRequired && (value == null || value.trim().isEmpty)) {
      return "El correo electrónico es obligatorio";
    }
    if (value != null && value.trim().isNotEmpty) {
      final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
      if (!emailRegex.hasMatch(value.trim())) {
        return "Ingresa un correo electrónico válido";
      }
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return CustomInput(
      label: label,
      hint: hint,
      prefixIcon: Icons.email_outlined,
      keyboardType: TextInputType.emailAddress,
      textInputAction: TextInputAction.next,
      controller: controller,
      fillColor: fillColor,
      validator: customValidator ?? _defaultEmailValidator,
      onChanged: onChanged,
    );
  }
}
