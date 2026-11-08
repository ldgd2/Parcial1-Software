import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Diálogo de Carga / Bloqueo Asíncrono (`CustomLoadingDialog`):
/// Ventana modal no cancelable para bloquear la interacción mientras se realiza
/// una petición pesada en backend (ej. "Procesando pago...", "Sincronizando datos...").
class CustomLoadingDialog extends StatelessWidget {
  final String message;

  const CustomLoadingDialog({
    super.key,
    this.message = "Cargando, por favor espera...",
  });

  /// Muestra el modal de carga bloqueante
  static Future<void> show(BuildContext context, {String message = "Cargando, por favor espera..."}) {
    return showGeneralDialog(
      context: context,
      barrierDismissible: false,
      barrierLabel: "LoadingDialog",
      barrierColor: Colors.black.withValues(alpha: 0.6),
      transitionDuration: const Duration(milliseconds: 200),
      pageBuilder: (ctx, anim1, anim2) => CustomLoadingDialog(message: message),
      transitionBuilder: (ctx, anim1, anim2, child) {
        return FadeTransition(
          opacity: anim1,
          child: ScaleTransition(
            scale: CurvedAnimation(parent: anim1, curve: Curves.easeOutBack),
            child: child,
          ),
        );
      },
    );
  }

  /// Cierra el modal de carga abierto
  static void hide(BuildContext context) {
    if (Navigator.of(context, rootNavigator: true).canPop()) {
      Navigator.of(context, rootNavigator: true).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    return PopScope(
      canPop: false,
      child: Dialog(
        backgroundColor: Colors.transparent,
        elevation: 0,
        insetPadding: const EdgeInsets.all(24),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 28),
          decoration: BoxDecoration(
            color: themeColores.fondoSecundario,
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.18),
                blurRadius: 24,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(
                width: 44,
                height: 44,
                child: CircularProgressIndicator(
                  strokeWidth: 3.5,
                  color: themeColores.primario,
                ),
              ),
              const SizedBox(height: 20),
              Text(
                message,
                textAlign: TextAlign.center,
                style: themeTextos.cuerpo.copyWith(
                  fontWeight: FontWeight.w600,
                  fontSize: 15,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
