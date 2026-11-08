import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import '../buttons/custom_button_primary.dart';
import '../buttons/custom_button_outline.dart';
import 'custom_dialog.dart';

/// Diálogo de Advertencia / Alerta (`CustomWarningDialog`):
/// Ventana modal para avisar sobre situaciones de riesgo o precaución
/// (ej. "Tu suscripción vence hoy", "Conexión inestable", "Cambios sin guardar").
class CustomWarningDialog extends StatelessWidget {
  final String title;
  final String message;
  final String confirmText;
  final String cancelText;
  final VoidCallback? onConfirm;
  final VoidCallback? onCancel;
  final IconData icon;

  const CustomWarningDialog({
    super.key,
    required this.title,
    required this.message,
    this.confirmText = "Entendido",
    this.cancelText = "Cancelar",
    this.onConfirm,
    this.onCancel,
    this.icon = Icons.warning_amber_rounded,
  });

  /// Método estático para mostrar rápidamente el diálogo de advertencia
  static Future<bool?> show({
    required BuildContext context,
    required String title,
    required String message,
    String confirmText = "Entendido",
    String cancelText = "Cancelar",
    VoidCallback? onConfirm,
    VoidCallback? onCancel,
    IconData icon = Icons.warning_amber_rounded,
  }) {
    return CustomDialog.show<bool>(
      context: context,
      builder: (ctx) => CustomWarningDialog(
        title: title,
        message: message,
        confirmText: confirmText,
        cancelText: cancelText,
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
  Widget build(BuildContext context) {
    final themeColores = context.colores;

    return CustomDialog(
      title: title,
      message: message,
      icon: icon,
      iconColor: themeColores.advertencia,
      iconBackgroundColor: themeColores.advertencia.withValues(alpha: 0.12),
      actions: [
        CustomOutlineButton(
          text: cancelText,
          onPressed: onCancel ?? () => Navigator.of(context).pop(false),
        ),
        const SizedBox(width: 12),
        CustomPrimaryButton(
          text: confirmText,
          backgroundColor: themeColores.advertencia,
          onPressed: onConfirm ?? () => Navigator.of(context).pop(true),
        ),
      ],
    );
  }
}
