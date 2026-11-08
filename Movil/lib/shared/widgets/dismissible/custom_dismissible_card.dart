import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import '../cards/custom_card.dart';
import '../dialogs/custom_dialog_danger.dart';
import 'custom_dismissible.dart';
import 'custom_dismissible_background.dart';

/// Tarjeta Deslizable de Lista (`CustomDismissibleCard`):
/// Tarjeta lista para usar en bandejas de entrada, listas de tareas, solicitudes, notificaciones o carritos.
/// Integra soporte para deslizar a la izquierda (borrar/rechazar) y a la derecha (archivar/aceptar).
class CustomDismissibleCard extends StatelessWidget {
  final Key itemKey;
  final String title;
  final String? subtitle;
  final String? time;
  final IconData? leadingIcon;
  final Color? leadingColor;
  final Widget? leadingWidget;
  final bool isUnread;
  final bool confirmOnDelete;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;
  final VoidCallback? onArchive;
  final VoidCallback? onAccept;
  final VoidCallback? onReject;
  final bool isDecisionMode;
  final double borderRadius;

  const CustomDismissibleCard({
    super.key,
    required this.itemKey,
    required this.title,
    this.subtitle,
    this.time,
    this.leadingIcon,
    this.leadingColor,
    this.leadingWidget,
    this.isUnread = false,
    this.confirmOnDelete = false,
    this.onTap,
    this.onDelete,
    this.onArchive,
    this.borderRadius = 16.0,
  })  : isDecisionMode = false,
        onAccept = null,
        onReject = null;

  /// Constructor específico para Decisiones y Solicitudes:
  /// Deslizar a la Derecha = Aceptar (Verde)
  /// Deslizar a la Izquierda = Rechazar (Rojo)
  const CustomDismissibleCard.decision({
    super.key,
    required this.itemKey,
    required this.title,
    this.subtitle,
    this.time,
    this.leadingIcon = Icons.person_add_alt_1_outlined,
    this.leadingColor,
    this.leadingWidget,
    this.isUnread = false,
    this.confirmOnDelete = false,
    this.onTap,
    required this.onAccept,
    required this.onReject,
    this.borderRadius = 16.0,
  })  : isDecisionMode = true,
        onDelete = onReject,
        onArchive = onAccept;

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    final background = isDecisionMode
        ? CustomDismissibleBackground.accept(borderRadius: borderRadius)
        : CustomDismissibleBackground.archive(borderRadius: borderRadius);

    final secondaryBackground = isDecisionMode
        ? CustomDismissibleBackground.reject(borderRadius: borderRadius)
        : CustomDismissibleBackground.delete(borderRadius: borderRadius);

    return CustomDismissible(
      dismissKey: itemKey,
      borderRadius: borderRadius,
      background: background,
      secondaryBackground: secondaryBackground,
      confirmDismiss: (dir) async {
        if (dir == DismissDirection.endToStart && confirmOnDelete) {
          final result = await CustomDangerDialog.show(
            context: context,
            title: isDecisionMode ? "¿Rechazar solicitud?" : "¿Eliminar elemento?",
            message: isDecisionMode
                ? "Esta acción rechazará y descartará esta solicitud."
                : "Esta acción quitará este elemento de tu lista.",
            confirmText: isDecisionMode ? "Rechazar" : "Eliminar",
          );
          return result ?? false;
        }
        return true;
      },
      onSwipeLeft: onDelete,
      onSwipeRight: onArchive,
      child: CustomCard(
        onTap: onTap,
        borderRadius: borderRadius,
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 14.0),
        child: Row(
          children: [
            // Indicador de no leído (Punto azul)
            if (isUnread) ...[
              Container(
                width: 8,
                height: 8,
                margin: const EdgeInsets.only(right: 10),
                decoration: BoxDecoration(
                  color: themeColores.primario,
                  shape: BoxShape.circle,
                ),
              ),
            ],

            // Icono o Widget Leading
            if (leadingWidget != null) ...[
              leadingWidget!,
              const SizedBox(width: 12),
            ] else if (leadingIcon != null) ...[
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: (leadingColor ?? themeColores.primario).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  leadingIcon,
                  color: leadingColor ?? themeColores.primario,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
            ],

            // Contenido textual (Título y Subtítulo)
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: themeTextos.cuerpo.copyWith(
                            fontWeight: isUnread ? FontWeight.bold : FontWeight.w600,
                            fontSize: 14.5,
                          ),
                        ),
                      ),
                      if (time != null) ...[
                        const SizedBox(width: 6),
                        Text(
                          time!,
                          style: themeTextos.cuerpoPequeno.copyWith(
                            fontSize: 11,
                            color: themeColores.textoSecundario,
                          ),
                        ),
                      ],
                    ],
                  ),
                  if (subtitle != null) ...[
                    const SizedBox(height: 3),
                    Text(
                      subtitle!,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: themeTextos.cuerpoPequeno.copyWith(
                        fontSize: 12.5,
                        color: themeColores.textoSecundario,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
