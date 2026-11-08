import 'package:flutter/material.dart';
import 'custom_input.dart';

/// Campo de Contraseña para Inicio de Sesión (`CustomPasswordInput`):
/// Oculta el texto por defecto con botón para ver/ocultar y validador de seguridad integrado.
class CustomPasswordInput extends StatefulWidget {
  final String hint;
  final String? label;
  final ValueChanged<String>? onChanged;
  final TextEditingController? controller;
  final Color? fillColor;
  final String? Function(String?)? validator;
  final bool validateRules;
  final bool isRequired;

  const CustomPasswordInput({
    super.key,
    this.hint = "••••••••",
    this.label = "Contraseña",
    this.onChanged,
    this.controller,
    this.fillColor,
    this.validator,
    this.validateRules = false,
    this.isRequired = true,
  });

  @override
  State<CustomPasswordInput> createState() => _CustomPasswordInputState();
}

class _CustomPasswordInputState extends State<CustomPasswordInput> {
  String? _validatePassword(String? value) {
    if (widget.validator != null) {
      return widget.validator!(value);
    }
    if (widget.isRequired && (value == null || value.trim().isEmpty)) {
      return "La contraseña es obligatoria";
    }
    if (widget.validateRules && value != null) {
      if (value.length < 8) {
        return "Debe tener al menos 8 caracteres";
      }
      if (!RegExp(r'[A-Z]').hasMatch(value)) {
        return "Debe contener al menos una mayúscula (A-Z)";
      }
      if (!RegExp(r'[a-z]').hasMatch(value)) {
        return "Debe contener al menos una minúscula (a-z)";
      }
      if (!RegExp(r'[0-9]').hasMatch(value)) {
        return "Debe contener al menos un número (0-9)";
      }
      if (!RegExp(r'[!@#\$%^&*(),.?":{}|<>]').hasMatch(value)) {
        return "Debe contener al menos un carácter especial (!@#\$)";
      }
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return CustomInput(
      hint: widget.hint,
      label: widget.label,
      prefixIcon: Icons.lock_outline,
      isPassword: true,
      fillColor: widget.fillColor,
      controller: widget.controller,
      validator: _validatePassword,
      onChanged: widget.onChanged,
    );
  }
}
