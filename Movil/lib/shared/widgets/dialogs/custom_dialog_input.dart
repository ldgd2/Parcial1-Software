import 'package:flutter/material.dart';
import '../buttons/custom_button_primary.dart';
import '../buttons/custom_button_outline.dart';
import '../inputs/custom_input.dart';
import 'custom_dialog.dart';

/// Diálogo con Campo de Entrada (`CustomInputDialog`):
/// Ventana modal para solicitar datos al usuario mediante un campo de texto
/// (ej. "Crear nueva carpeta", "Ingresar código de descuento", "Renombrar archivo").
class CustomInputDialog extends StatefulWidget {
  final String title;
  final String? message;
  final String hint;
  final String? initialValue;
  final String confirmText;
  final String cancelText;
  final IconData? icon;
  final ValueChanged<String>? onConfirm;
  final VoidCallback? onCancel;
  final TextInputType keyboardType;

  const CustomInputDialog({
    super.key,
    required this.title,
    this.message,
    this.hint = "Escribe aquí...",
    this.initialValue,
    this.confirmText = "Aceptar",
    this.cancelText = "Cancelar",
    this.icon = Icons.edit_outlined,
    this.onConfirm,
    this.onCancel,
    this.keyboardType = TextInputType.text,
  });

  /// Método estático para solicitar rápidamente texto al usuario
  static Future<String?> show({
    required BuildContext context,
    required String title,
    String? message,
    String hint = "Escribe aquí...",
    String? initialValue,
    String confirmText = "Aceptar",
    String cancelText = "Cancelar",
    IconData? icon = Icons.edit_outlined,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return CustomDialog.show<String>(
      context: context,
      builder: (ctx) => CustomInputDialog(
        title: title,
        message: message,
        hint: hint,
        initialValue: initialValue,
        confirmText: confirmText,
        cancelText: cancelText,
        icon: icon,
        keyboardType: keyboardType,
        onConfirm: (val) => Navigator.of(ctx).pop(val),
        onCancel: () => Navigator.of(ctx).pop(null),
      ),
    );
  }

  @override
  State<CustomInputDialog> createState() => _CustomInputDialogState();
}

class _CustomInputDialogState extends State<CustomInputDialog> {
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialValue);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return CustomDialog(
      title: widget.title,
      message: widget.message,
      icon: widget.icon,
      content: CustomInput(
        hint: widget.hint,
        controller: _controller,
        keyboardType: widget.keyboardType,
      ),
      actions: [
        CustomOutlineButton(
          text: widget.cancelText,
          onPressed: widget.onCancel ?? () => Navigator.of(context).pop(null),
        ),
        const SizedBox(width: 12),
        CustomPrimaryButton(
          text: widget.confirmText,
          onPressed: () {
            final text = _controller.text.trim();
            if (widget.onConfirm != null) {
              widget.onConfirm!(text);
            } else {
              Navigator.of(context).pop(text);
            }
          },
        ),
      ],
    );
  }
}
