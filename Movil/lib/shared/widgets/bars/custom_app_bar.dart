import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Barra Superior Estandarizada (`CustomAppBar`):
/// Proporciona un `AppBar` modular y estilizado con soporte de subtítulos, botones de retroceso,
/// acciones personalizadas y estilo coherente con el sistema de diseño.
class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final String? subtitle;
  final Widget? leading;
  final List<Widget>? actions;
  final bool centerTitle;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final double elevation;
  final PreferredSizeWidget? bottom;
  final VoidCallback? onBack;

  const CustomAppBar({
    super.key,
    required this.title,
    this.subtitle,
    this.leading,
    this.actions,
    this.centerTitle = false,
    this.backgroundColor,
    this.foregroundColor,
    this.elevation = 0.0,
    this.bottom,
    this.onBack,
  });

  @override
  Size get preferredSize => Size.fromHeight(kToolbarHeight + (bottom?.preferredSize.height ?? 0.0));

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    final resolvedBg = backgroundColor ?? themeColores.primario;
    final resolvedFg = foregroundColor ?? Colors.white;

    Widget? leadingWidget = leading;
    if (leadingWidget == null && (Navigator.canPop(context) || onBack != null)) {
      leadingWidget = IconButton(
        icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
        color: resolvedFg,
        onPressed: onBack ?? () => Navigator.maybePop(context),
      );
    }

    return AppBar(
      backgroundColor: resolvedBg,
      foregroundColor: resolvedFg,
      elevation: elevation,
      centerTitle: centerTitle,
      leading: leadingWidget,
      actions: actions,
      bottom: bottom,
      title: Column(
        crossAxisAlignment: centerTitle ? CrossAxisAlignment.center : CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            title,
            style: themeTextos.titulo.copyWith(
              color: resolvedFg,
              fontSize: 18.5,
              fontWeight: FontWeight.bold,
            ),
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 2),
            Text(
              subtitle!,
              style: themeTextos.cuerpoPequeno.copyWith(
                color: resolvedFg.withValues(alpha: 0.8),
                fontSize: 12,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
