import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_input.dart';

/// Campo de Moneda / Montos (`CustomCurrencyInput`):
/// Entrada optimizada para transacciones financieras, presupuestos y precios con símbolo de moneda.
class CustomCurrencyInput extends StatelessWidget {
  final String? label;
  final String hint;
  final String currencySymbol;
  final ValueChanged<String>? onChanged;
  final TextEditingController? controller;
  final String? Function(String?)? validator;
  final Color? fillColor;
  final double? maxAmount;

  const CustomCurrencyInput({
    super.key,
    this.label = "Monto",
    this.hint = "0.00",
    this.currencySymbol = "\$",
    this.onChanged,
    this.controller,
    this.validator,
    this.fillColor,
    this.maxAmount,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;

    final prefix = Padding(
      padding: const EdgeInsets.only(left: 16, right: 8),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            currencySymbol,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: themeColores.primario,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            width: 1,
            height: 22,
            color: themeColores.borde.withValues(alpha: 0.8),
          ),
        ],
      ),
    );

    return CustomInput(
      label: label,
      hint: hint,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      prefixWidget: prefix,
      controller: controller,
      fillColor: fillColor,
      validator: validator,
      inputFormatters: [
        FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,2}')),
      ],
      onChanged: onChanged,
    );
  }
}
