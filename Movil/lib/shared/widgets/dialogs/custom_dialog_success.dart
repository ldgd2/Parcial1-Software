import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import '../buttons/custom_button_primary.dart';
import 'custom_dialog.dart';

/// Diálogo de Éxito (`CustomSuccessDialog`):
/// Ventana modal para felicitar al usuario o confirmar que una operación se completó exitosamente
/// (ej. "¡Pago Exitoso!", "Perfil Actualizado", "Descarga Completada").
class CustomSuccessDialog extends StatelessWidget {
  final String title;
  final String message;
  final String buttonText;
  final VoidCallback? onPressed;
  final IconData icon;

  const CustomSuccessDialog({
    super.key,
    required this.title,
    required this.message,
    this.buttonText = "Aceptar",
    this.onPressed,
    this.icon = Icons.check_circle_outline_rounded,
  });

  /// Método estático para mostrar rápidamente el diálogo de éxito
  static Future<void> show({
    required BuildContext context,
    required String title,
    required String message,
    String buttonText = "Aceptar",
    VoidCallback? onPressed,
    IconData icon = Icons.check_circle_outline_rounded,
  }) {
    return CustomDialog.show(
      context: context,
      builder: (ctx) => CustomSuccessDialog(
        title: title,
        message: message,
        buttonText: buttonText,
        icon: icon,
        onPressed: () {
          Navigator.of(ctx).pop();
          onPressed?.call();
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
      iconColor: themeColores.exito,
      iconBackgroundColor: themeColores.exito.withValues(alpha: 0.12),
      actions: [
        CustomPrimaryButton(
          text: buttonText,
          backgroundColor: themeColores.exito,
          isFullWidth: true,
          onPressed: onPressed ?? () => Navigator.of(context).pop(),
        ),
      ],
    );
  }
}
