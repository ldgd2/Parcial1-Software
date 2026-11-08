import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import '../buttons/custom_button_primary.dart';
import 'custom_dialog.dart';

/// Diálogo Informativo (`CustomInfoDialog`):
/// Ventana modal para mostrar información general, avisos del sistema, novedades o políticas
/// (ej. "Nueva actualización disponible", "Términos del servicio", "Mantenimiento programado").
class CustomInfoDialog extends StatelessWidget {
  final String title;
  final String message;
  final String buttonText;
  final VoidCallback? onPressed;
  final IconData icon;

  const CustomInfoDialog({
    super.key,
    required this.title,
    required this.message,
    this.buttonText = "Entendido",
    this.onPressed,
    this.icon = Icons.info_outline_rounded,
  });

  /// Método estático para mostrar rápidamente el diálogo informativo
  static Future<void> show({
    required BuildContext context,
    required String title,
    required String message,
    String buttonText = "Entendido",
    VoidCallback? onPressed,
    IconData icon = Icons.info_outline_rounded,
  }) {
    return CustomDialog.show(
      context: context,
      builder: (ctx) => CustomInfoDialog(
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
      iconColor: themeColores.primario,
      actions: [
        CustomPrimaryButton(
          text: buttonText,
          isFullWidth: true,
          onPressed: onPressed ?? () => Navigator.of(context).pop(),
        ),
      ],
    );
  }
}
