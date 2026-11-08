import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import '../buttons/custom_button_danger.dart';
import '../buttons/custom_button_outline.dart';
import '../inputs/custom_input.dart';
import 'custom_dialog.dart';

/// Diálogo de Acción Crítica / Destructiva (`CustomDangerDialog`):
/// Diseñado para operaciones irreversibles (eliminar cuenta, borrar base de datos, desvincular).
/// Alerta visual en color rojo/error con opción de verificación de texto de seguridad.
class CustomDangerDialog extends StatefulWidget {
  final String title;
  final String message;
  final String confirmText;
  final String cancelText;
  final String? requireConfirmationWord;
  final VoidCallback? onConfirm;
  final VoidCallback? onCancel;
  final IconData icon;

  const CustomDangerDialog({
    super.key,
    required this.title,
    required this.message,
    this.confirmText = "Eliminar",
    this.cancelText = "Cancelar",
    this.requireConfirmationWord,
    this.onConfirm,
    this.onCancel,
    this.icon = Icons.delete_forever_rounded,
  });

  /// Método estático para mostrar rápidamente el diálogo crítico/destructivo
  static Future<bool?> show({
    required BuildContext context,
    required String title,
    required String message,
    String confirmText = "Eliminar",
    String cancelText = "Cancelar",
    String? requireConfirmationWord,
    VoidCallback? onConfirm,
    VoidCallback? onCancel,
    IconData icon = Icons.delete_forever_rounded,
  }) {
    return CustomDialog.show<bool>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => CustomDangerDialog(
        title: title,
        message: message,
        confirmText: confirmText,
        cancelText: cancelText,
        requireConfirmationWord: requireConfirmationWord,
        icon: icon,
        onConfirm: () {
          Navigator.of(ctx).pop(true);
          onConfirm?.call();
        },
        onCancel: () {
          Navigator.of(ctx).pop(false);
          onCancel?.call();
        },
      ),
    );
  }

  @override
  State<CustomDangerDialog> createState() => _CustomDangerDialogState();
}

class _CustomDangerDialogState extends State<CustomDangerDialog> {
  final TextEditingController _controller = TextEditingController();
  bool _isConfirmed = false;

  @override
  void initState() {
    super.initState();
    _isConfirmed = widget.requireConfirmationWord == null;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    return CustomDialog(
      title: widget.title,
      message: widget.message,
      icon: widget.icon,
      iconColor: themeColores.error,
      iconBackgroundColor: themeColores.error.withValues(alpha: 0.12),
      content: widget.requireConfirmationWord != null
          ? Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  "Escribe '${widget.requireConfirmationWord}' para confirmar:",
                  style: themeTextos.cuerpoPequeno.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                CustomInput(
                  hint: widget.requireConfirmationWord!,
                  controller: _controller,
                  fillColor: themeColores.borde.withValues(alpha: 0.25),
                  onChanged: (val) {
                    setState(() {
                      _isConfirmed = val.trim().toLowerCase() ==
                          widget.requireConfirmationWord!.trim().toLowerCase();
                    });
                  },
                ),
              ],
            )
          : null,
      actions: [
        CustomOutlineButton(
          text: widget.cancelText,
          onPressed: widget.onCancel ?? () => Navigator.of(context).pop(false),
        ),
        const SizedBox(width: 12),
        CustomDangerButton(
          text: widget.confirmText,
          isDisabled: !_isConfirmed,
          onPressed: _isConfirmed
              ? (widget.onConfirm ?? () => Navigator.of(context).pop(true))
              : null,
        ),
      ],
    );
  }
}
