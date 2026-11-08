import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Barra Superior con Búsqueda Integrada (`CustomSearchAppBar`):
/// Ideal para pantallas de catálogo, directorios, mensajería o exploración de listas.
class CustomSearchAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String hint;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final VoidCallback? onClear;
  final VoidCallback? onFilterTap;
  final VoidCallback? onBack;
  final TextEditingController? controller;
  final Color? backgroundColor;
  final Color? searchBarColor;
  final bool autofocus;

  const CustomSearchAppBar({
    super.key,
    this.hint = "Buscar...",
    this.onChanged,
    this.onSubmitted,
    this.onClear,
    this.onFilterTap,
    this.onBack,
    this.controller,
    this.backgroundColor,
    this.searchBarColor,
    this.autofocus = false,
  });

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight + 8.0);

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    final resolvedBg = backgroundColor ?? themeColores.fondoSecundario;
    final resolvedBarBg = searchBarColor ?? themeColores.fondo;

    return AppBar(
      backgroundColor: resolvedBg,
      elevation: 0,
      titleSpacing: 0,
      leading: IconButton(
        icon: Icon(Icons.arrow_back_ios_new_rounded, color: themeColores.textoPrincipal, size: 20),
        onPressed: onBack ?? () => Navigator.maybePop(context),
      ),
      title: Container(
        height: 42,
        margin: const EdgeInsets.only(right: 16),
        decoration: BoxDecoration(
          color: resolvedBarBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: themeColores.borde.withValues(alpha: 0.5), width: 1),
        ),
        child: TextField(
          controller: controller,
          autofocus: autofocus,
          onChanged: onChanged,
          onSubmitted: onSubmitted,
          textInputAction: TextInputAction.search,
          style: themeTextos.cuerpo.copyWith(fontSize: 14),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: themeTextos.cuerpoPequeno.copyWith(color: themeColores.textoSecundario),
            prefixIcon: Icon(Icons.search_rounded, color: themeColores.textoSecundario, size: 20),
            suffixIcon: controller != null && controller!.text.isNotEmpty
                ? IconButton(
                    icon: Icon(Icons.close_rounded, color: themeColores.textoSecundario, size: 18),
                    onPressed: () {
                      controller?.clear();
                      onClear?.call();
                      onChanged?.call("");
                    },
                  )
                : (onFilterTap != null
                    ? IconButton(
                        icon: Icon(Icons.tune_rounded, color: themeColores.primario, size: 20),
                        onPressed: onFilterTap,
                      )
                    : null),
            border: InputBorder.none,
            contentPadding: const EdgeInsets.symmetric(vertical: 10),
          ),
        ),
      ),
    );
  }
}
