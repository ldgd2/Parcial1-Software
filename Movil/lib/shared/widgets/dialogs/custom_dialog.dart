import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Diálogo Base (`CustomDialog`):
/// Ventana modal emergente en el centro de la pantalla que bloquea la interacción con el fondo.
/// Diseñada con estética premium, bordes redondeados, soporte para iconos destacados,
/// títulos, descripciones, contenido personalizado y fila/columna de botones de acción.
class CustomDialog extends StatelessWidget {
  final String title;
  final String? message;
  final Widget? content;
  final IconData? icon;
  final Color? iconColor;
  final Color? iconBackgroundColor;
  final List<Widget>? actions;
  final double borderRadius;
  final double maxWidth;
  final EdgeInsetsGeometry padding;
  final Color? backgroundColor;
  final bool showCloseButton;
  final VoidCallback? onClose;

  const CustomDialog({
    super.key,
    required this.title,
    this.message,
    this.content,
    this.icon,
    this.iconColor,
    this.iconBackgroundColor,
    this.actions,
    this.borderRadius = 24.0,
    this.maxWidth = 380.0,
    this.padding = const EdgeInsets.all(24.0),
    this.backgroundColor,
    this.showCloseButton = false,
    this.onClose,
  });

  /// Método estático para mostrar cualquier CustomDialog fácilmente
  static Future<T?> show<T>({
    required BuildContext context,
    required WidgetBuilder builder,
    bool barrierDismissible = true,
    Color? barrierColor,
  }) {
    return showGeneralDialog<T>(
      context: context,
      barrierDismissible: barrierDismissible,
      barrierLabel: "DismissDialog",
      barrierColor: barrierColor ?? Colors.black.withValues(alpha: 0.55),
      transitionDuration: const Duration(milliseconds: 220),
      pageBuilder: (ctx, anim1, anim2) => builder(ctx),
      transitionBuilder: (ctx, anim1, anim2, child) {
        final curvedAnim = CurvedAnimation(parent: anim1, curve: Curves.easeOutBack);
        return ScaleTransition(
          scale: curvedAnim,
          child: FadeTransition(
            opacity: anim1,
            child: child,
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    final resolvedBg = backgroundColor ?? themeColores.fondoSecundario;
    final resolvedIconColor = iconColor ?? themeColores.primario;
    final resolvedIconBg = iconBackgroundColor ?? resolvedIconColor.withValues(alpha: 0.12);

    return Dialog(
      backgroundColor: Colors.transparent,
      elevation: 0,
      insetPadding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 24.0),
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: resolvedBg,
            borderRadius: BorderRadius.circular(borderRadius),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.18),
                blurRadius: 28,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Stack(
            children: [
              // Botón de cerrar superior opcional
              if (showCloseButton)
                Positioned(
                  top: -8,
                  right: -8,
                  child: IconButton(
                    icon: Icon(Icons.close, color: themeColores.textoSecundario, size: 20),
                    onPressed: onClose ?? () => Navigator.of(context).pop(),
                  ),
                ),

              // Contenido principal del diálogo
              Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // Icono en badge circular destacado
                  if (icon != null) ...[
                    Container(
                      width: 60,
                      height: 60,
                      decoration: BoxDecoration(
                        color: resolvedIconBg,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        icon,
                        color: resolvedIconColor,
                        size: 30,
                      ),
                    ),
                    const SizedBox(height: 18),
                  ],

                  // Título principal
                  Text(
                    title,
                    textAlign: TextAlign.center,
                    style: themeTextos.titulo.copyWith(
                      fontSize: 19,
                      fontWeight: FontWeight.bold,
                      letterSpacing: -0.3,
                    ),
                  ),

                  // Mensaje / Descripción
                  if (message != null) ...[
                    const SizedBox(height: 10),
                    Text(
                      message!,
                      textAlign: TextAlign.center,
                      style: themeTextos.cuerpoPequeno.copyWith(
                        color: themeColores.textoSecundario,
                        fontSize: 14,
                        height: 1.4,
                      ),
                    ),
                  ],

                  // Contenido personalizado (Inputs, listas, etc.)
                  if (content != null) ...[
                    const SizedBox(height: 16),
                    content!,
                  ],

                  // Botones de acción
                  if (actions != null && actions!.isNotEmpty) ...[
                    const SizedBox(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: actions!.map((action) => Expanded(child: action)).toList(),
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
