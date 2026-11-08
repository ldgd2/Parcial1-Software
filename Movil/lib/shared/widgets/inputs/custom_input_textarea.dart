import 'package:flutter/material.dart';
import 'custom_input.dart';

/// Área de Texto Multilínea (`CustomTextAreaInput`):
/// Diseñado para biografías, comentarios, descripciones y notas largas con contador de caracteres.
class CustomTextAreaInput extends StatelessWidget {
  final String? label;
  final String hint;
  final int minLines;
  final int maxLines;
  final int? maxLength;
  final ValueChanged<String>? onChanged;
  final TextEditingController? controller;
  final String? Function(String?)? validator;
  final Color? fillColor;

  const CustomTextAreaInput({
    super.key,
    this.label = "Descripción o Comentarios",
    this.hint = "Escribe aquí los detalles...",
    this.minLines = 3,
    this.maxLines = 6,
    this.maxLength = 500,
    this.onChanged,
    this.controller,
    this.validator,
    this.fillColor,
  });

  @override
  Widget build(BuildContext context) {
    return CustomInput(
      label: label,
      hint: hint,
      minLines: minLines,
      maxLines: maxLines,
      maxLength: maxLength,
      keyboardType: TextInputType.multiline,
      textInputAction: TextInputAction.newline,
      controller: controller,
      validator: validator,
      fillColor: fillColor,
      onChanged: onChanged,
    );
  }
}
