import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_input.dart';

/// Campo de Teléfono Internacional (`CustomPhoneInput`):
/// Incluye prefijo de código de país seleccionable y formato para números móviles.
class CustomPhoneInput extends StatefulWidget {
  final String? label;
  final String hint;
  final String initialCountryCode;
  final List<String> supportedCountryCodes;
  final ValueChanged<String>? onChanged;
  final TextEditingController? controller;
  final String? Function(String?)? validator;
  final Color? fillColor;

  const CustomPhoneInput({
    super.key,
    this.label = "Número de Teléfono",
    this.hint = "Ej. 412 123 4567",
    this.initialCountryCode = "+58",
    this.supportedCountryCodes = const ["+1", "+34", "+52", "+57", "+58", "+54", "+56", "+51"],
    this.onChanged,
    this.controller,
    this.validator,
    this.fillColor,
  });

  @override
  State<CustomPhoneInput> createState() => _CustomPhoneInputState();
}

class _CustomPhoneInputState extends State<CustomPhoneInput> {
  late String _selectedCountryCode;

  @override
  void initState() {
    super.initState();
    _selectedCountryCode = widget.initialCountryCode;
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;

    final prefix = Container(
      padding: const EdgeInsets.only(left: 12, right: 8),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: _selectedCountryCode,
          icon: Icon(Icons.keyboard_arrow_down, size: 18, color: themeColores.textoSecundario),
          items: widget.supportedCountryCodes.map((code) {
            return DropdownMenuItem(
              value: code,
              child: Text(
                code,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                  color: themeColores.textoPrincipal,
                ),
              ),
            );
          }).toList(),
          onChanged: (val) {
            if (val != null) {
              setState(() => _selectedCountryCode = val);
            }
          },
        ),
      ),
    );

    return CustomInput(
      label: widget.label,
      hint: widget.hint,
      keyboardType: TextInputType.phone,
      prefixWidget: prefix,
      controller: widget.controller,
      fillColor: widget.fillColor,
      validator: widget.validator,
      inputFormatters: [
        FilteringTextInputFormatter.digitsOnly,
      ],
      onChanged: (val) {
        widget.onChanged?.call("$_selectedCountryCode $val");
      },
    );
  }
}
