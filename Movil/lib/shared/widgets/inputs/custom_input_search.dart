import 'package:flutter/material.dart';
import 'custom_input.dart';

/// Barra de Búsqueda Especializada (`CustomSearchInput`):
/// Incluye icono de lupa, teclado de búsqueda (`TextInputAction.search`),
/// botón "X" dinámico para limpiar y opción de bordes redondeados tipo píldora.
class CustomSearchInput extends CustomInput {
  const CustomSearchInput({
    super.key,
    super.hint = "Buscar en la aplicación...",
    super.label,
    super.onChanged,
    super.onSubmitted,
    super.onClear,
    super.controller,
    super.fillColor,
    super.autofocus = false,
  }) : super(
          isSearch: true,
          prefixIcon: Icons.search,
          keyboardType: TextInputType.text,
          textInputAction: TextInputAction.search,
        );
}
