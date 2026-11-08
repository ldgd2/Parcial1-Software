import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'custom_dismissible_background.dart';

/// Envoltorio Deslizable (`CustomDismissible`):
/// Permite que cualquier tarjeta, fila o componente se deslice hacia la izquierda o derecha
/// para ejecutar acciones de borrado, archivado, aprobación o marcado con animación fluida.
class CustomDismissible extends StatelessWidget {
  final Key dismissKey;
  final Widget child;
  final Widget? background;
  final Widget? secondaryBackground;
  final Future<bool?> Function(DismissDirection)? confirmDismiss;
  final ValueChanged<DismissDirection>? onDismissed;
  final VoidCallback? onSwipeLeft;
  final VoidCallback? onSwipeRight;
  final DismissDirection direction;
  final double borderRadius;
  final bool enableHapticFeedback;
  final double dismissThreshold;
  final EdgeInsetsGeometry margin;

  const CustomDismissible({
    super.key,
    required this.dismissKey,
    required this.child,
    this.background,
    this.secondaryBackground,
    this.confirmDismiss,
    this.onDismissed,
    this.onSwipeLeft,
    this.onSwipeRight,
    this.direction = DismissDirection.horizontal,
    this.borderRadius = 16.0,
    this.enableHapticFeedback = true,
    this.dismissThreshold = 0.35,
    this.margin = EdgeInsets.zero,
  });

  /// Constructor estándar universal: Deslizar a la Derecha (Aceptar/Aprobar) y a la Izquierda (Rechazar/Eliminar)
  factory CustomDismissible.decision({
    required Key key,
    required Widget child,
    VoidCallback? onAccept,
    VoidCallback? onReject,
    String acceptLabel = "Aceptar",
    String rejectLabel = "Rechazar",
    Future<bool?> Function(DismissDirection)? confirmDismiss,
    double borderRadius = 16.0,
    EdgeInsetsGeometry margin = EdgeInsets.zero,
  }) {
    return CustomDismissible(
      dismissKey: key,
      background: CustomDismissibleBackground.accept(label: acceptLabel, borderRadius: borderRadius),
      secondaryBackground: CustomDismissibleBackground.reject(label: rejectLabel, borderRadius: borderRadius),
      direction: (onAccept != null && onReject != null)
          ? DismissDirection.horizontal
          : (onReject != null
              ? DismissDirection.endToStart
              : DismissDirection.startToEnd),
      confirmDismiss: confirmDismiss,
      onSwipeRight: onAccept,
      onSwipeLeft: onReject,
      borderRadius: borderRadius,
      margin: margin,
      child: child,
    );
  }

  /// Constructor rápido para Deslizar a la izquierda (Borrar) y derecha (Archivar) estilo Gmail
  factory CustomDismissible.emailStyle({
    required Key key,
    required Widget child,
    VoidCallback? onDelete,
    VoidCallback? onArchive,
    Future<bool?> Function(DismissDirection)? confirmDismiss,
    double borderRadius = 16.0,
    EdgeInsetsGeometry margin = EdgeInsets.zero,
  }) {
    return CustomDismissible(
      dismissKey: key,
      background: CustomDismissibleBackground.archive(borderRadius: borderRadius),
      secondaryBackground: CustomDismissibleBackground.delete(borderRadius: borderRadius),
      direction: (onArchive != null && onDelete != null)
          ? DismissDirection.horizontal
          : (onDelete != null
              ? DismissDirection.endToStart
              : DismissDirection.startToEnd),
      confirmDismiss: confirmDismiss,
      onSwipeLeft: onDelete,
      onSwipeRight: onArchive,
      borderRadius: borderRadius,
      margin: margin,
      child: child,
    );
  }

  /// Constructor rápido solo para Borrar (Deslizar hacia la izquierda)
  factory CustomDismissible.deleteOnly({
    required Key key,
    required Widget child,
    required VoidCallback onDelete,
    Future<bool?> Function(DismissDirection)? confirmDismiss,
    double borderRadius = 16.0,
    EdgeInsetsGeometry margin = EdgeInsets.zero,
  }) {
    return CustomDismissible(
      dismissKey: key,
      secondaryBackground: CustomDismissibleBackground.delete(borderRadius: borderRadius),
      direction: DismissDirection.endToStart,
      confirmDismiss: confirmDismiss,
      onSwipeLeft: onDelete,
      borderRadius: borderRadius,
      margin: margin,
      child: child,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: Dismissible(
          key: dismissKey,
          direction: direction,
          background: background ?? CustomDismissibleBackground.archive(borderRadius: borderRadius),
          secondaryBackground:
              secondaryBackground ?? CustomDismissibleBackground.delete(borderRadius: borderRadius),
          dismissThresholds: {
            DismissDirection.startToEnd: dismissThreshold,
            DismissDirection.endToStart: dismissThreshold,
          },
          confirmDismiss: (dir) async {
            if (enableHapticFeedback) {
              HapticFeedback.mediumImpact();
            }
            if (confirmDismiss != null) {
              return await confirmDismiss!(dir);
            }
            return true;
          },
          onDismissed: (dir) {
            if (dir == DismissDirection.endToStart) {
              onSwipeLeft?.call();
            } else if (dir == DismissDirection.startToEnd) {
              onSwipeRight?.call();
            }
            onDismissed?.call(dir);
          },
          child: child,
        ),
      ),
    );
  }
}
