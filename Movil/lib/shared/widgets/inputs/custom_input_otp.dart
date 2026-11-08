import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../utils/ui_engine/tema.dart';

/// Campo de Código de Verificación OTP (`CustomOtpInput`):
/// Grupos de 4 a 6 casillas cuadradas separadas para introducir códigos SMS o 2FA.
/// Soporta auto-avance entre casillas, retroceso con backspace y pegado del código completo.
class CustomOtpInput extends StatefulWidget {
  final int length;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onCompleted;
  final bool isObscure;
  final double fieldWidth;
  final double fieldHeight;
  final Color? fillColor;
  final Color? activeBorderColor;
  final bool autofocus;

  const CustomOtpInput({
    super.key,
    this.length = 6,
    this.onChanged,
    this.onCompleted,
    this.isObscure = false,
    this.fieldWidth = 48.0,
    this.fieldHeight = 54.0,
    this.fillColor,
    this.activeBorderColor,
    this.autofocus = true,
  }) : assert(length >= 4 && length <= 8, "La longitud del OTP debe estar entre 4 y 8");

  @override
  State<CustomOtpInput> createState() => _CustomOtpInputState();
}

class _CustomOtpInputState extends State<CustomOtpInput> {
  late List<TextEditingController> _controllers;
  late List<FocusNode> _focusNodes;

  @override
  void initState() {
    super.initState();
    _controllers = List.generate(widget.length, (_) => TextEditingController());
    _focusNodes = List.generate(widget.length, (_) => FocusNode());
  }

  @override
  void dispose() {
    for (final c in _controllers) {
      c.dispose();
    }
    for (final f in _focusNodes) {
      f.dispose();
    }
    super.dispose();
  }

  String get _currentOtp => _controllers.map((c) => c.text).join();

  void _onChanged(String value, int index) {
    if (value.length > 1) {
      // Manejo de pegado (Paste) de código completo
      final cleanText = value.replaceAll(RegExp(r'[^0-9]'), '');
      for (int i = 0; i < widget.length; i++) {
        if (i < cleanText.length) {
          _controllers[i].text = cleanText[i];
        }
      }
      _focusNodes.last.requestFocus();
    } else if (value.isNotEmpty) {
      // Avanzar al siguiente recuadro
      if (index < widget.length - 1) {
        _focusNodes[index + 1].requestFocus();
      } else {
        _focusNodes[index].unfocus();
      }
    }

    final code = _currentOtp;
    widget.onChanged?.call(code);

    if (code.length == widget.length) {
      widget.onCompleted?.call(code);
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final resolvedFill = widget.fillColor ?? themeColores.fondoSecundario;
    final resolvedActiveBorder = widget.activeBorderColor ?? themeColores.primario;

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(widget.length, (index) {
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 4),
          width: widget.fieldWidth,
          height: widget.fieldHeight,
          child: KeyboardListener(
            focusNode: FocusNode(),
            onKeyEvent: (event) {
              // Retroceder al borrar con backspace si está vacío
              if (event is KeyDownEvent &&
                  event.logicalKey == LogicalKeyboardKey.backspace &&
                  _controllers[index].text.isEmpty &&
                  index > 0) {
                _focusNodes[index - 1].requestFocus();
              }
            },
            child: TextField(
              controller: _controllers[index],
              focusNode: _focusNodes[index],
              autofocus: widget.autofocus && index == 0,
              textAlign: TextAlign.center,
              keyboardType: TextInputType.number,
              obscureText: widget.isObscure,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: themeColores.textoPrincipal,
              ),
              inputFormatters: [
                LengthLimitingTextInputFormatter(widget.length), // Permite capturar pegados
                FilteringTextInputFormatter.digitsOnly,
              ],
              onChanged: (val) => _onChanged(val, index),
              decoration: InputDecoration(
                filled: true,
                fillColor: resolvedFill,
                counterText: "",
                contentPadding: EdgeInsets.zero,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: themeColores.borde.withValues(alpha: 0.5)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: themeColores.borde.withValues(alpha: 0.6)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: resolvedActiveBorder, width: 2),
                ),
              ),
            ),
          ),
        );
      }),
    );
  }
}
