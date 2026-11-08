import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'custom_input.dart';

/// Campo Numérico (`CustomNumberInput`):
/// Abre el teclado numérico nativo en móvil y bloquea estrictamente cualquier letra o símbolo no numérico.
class CustomNumberInput extends CustomInput {
  CustomNumberInput({
    super.key,
    required super.hint,
    super.label,
    super.onChanged,
    super.fillColor,
    super.controller,
    super.validator,
    bool allowDecimals = false,
  }) : super(
          keyboardType: TextInputType.numberWithOptions(
            decimal: allowDecimals,
            signed: false,
          ),
          prefixIcon: Icons.pin_outlined,
          inputFormatters: [
            if (allowDecimals)
              FilteringTextInputFormatter.allow(RegExp(r'[0-9.]'))
            else
              FilteringTextInputFormatter.digitsOnly,
          ],
        );
}
