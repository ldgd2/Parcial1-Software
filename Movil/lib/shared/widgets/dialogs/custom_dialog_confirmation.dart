import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import '../buttons/custom_button_primary.dart';
import '../buttons/custom_button_outline.dart';
import 'custom_dialog.dart';

/// Diálogo de Confirmación (`CustomConfirmationDialog`):
/// Ventana modal para solicitar la aprobación del usuario antes de proceder
/// con una acción (ej. "¿Deseas guardar los cambios?", "¿Cerrar sesión?").
class CustomConfirmationDialog extends StatelessWidget {
  final String title;
  final String message;
  final String confirmText;
  final String cancelText;
  final VoidCallback? onConfirm;
  final VoidCallback? onCancel;
  final IconData icon;
  final Color? iconColor;

  const CustomConfirmationDialog({
    super.key,
    required this.title,
    required this.message,
    this.confirmText = "Confirmar",
    this.cancelText = "Cancelar",
    this.onConfirm,
    this.onCancel,
    this.icon = Icons.help_outline_rounded,
    this.iconColor,
  });

  /// Método estático para mostrar rápidamente el diálogo de confirmación
  static Future<bool?> show({
    required BuildContext context,
    required String title,
    required String message,
    String confirmText = "Confirmar",
    String cancelText = "Cancelar",
    VoidCallback? onConfirm,
    VoidCallback? onCancel,
    IconData icon = Icons.help_outline_rounded,
    Color? iconColor,
  }) {
    return CustomDialog.show<bool>(
      context: context,
      builder: (ctx) => CustomConfirmationDialog(
        title: title,
        message: message,
        confirmText: confirmText,
        cancelText: cancelText,
        icon: icon,
        iconColor: iconColor,
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
  Widget build(BuildContext context) {
    final themeColores = context.colores;

    return CustomDialog(
      title: title,
      message: message,
      icon: icon,
      iconColor: iconColor ?? themeColores.primario,
      actions: [
        CustomOutlineButton(
          text: cancelText,
          onPressed: onCancel ?? () => Navigator.of(context).pop(false),
        ),
        const SizedBox(width: 12),
        CustomPrimaryButton(
          text: confirmText,
          onPressed: onConfirm ?? () => Navigator.of(context).pop(true),
        ),
      ],
    );
  }
}
