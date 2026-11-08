import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Campo selector base (Base Picker Field) que estandariza la apariencia visual
/// de los selectores táctiles en la aplicación móvil.
/// Muestra el valor seleccionado, iconos contextuales y abre modales/bottom sheets al presionar.
class CustomPickerField extends StatelessWidget {
  final String hint;
  final String? label;
  final String? valueText;
  final VoidCallback? onTap;
  final VoidCallback? onClear;
  final IconData? prefixIcon;
  final Widget? suffixIcon;
  final Color? fillColor;
  final bool isDisabled;
  final String? errorText;
  final double borderRadius;

  const CustomPickerField({
    super.key,
    required this.hint,
    this.label,
    this.valueText,
    this.onTap,
    this.onClear,
    this.prefixIcon,
    this.suffixIcon,
    this.fillColor,
    this.isDisabled = false,
    this.errorText,
    this.borderRadius = 12.0,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;
    final bool hasValue = valueText != null && valueText!.isNotEmpty;
    final actualFillColor = fillColor ?? themeColores.borde.withValues(alpha: 0.3);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (label != null) ...[
          Text(
            label!,
            style: themeTextos.cuerpoPequeno.copyWith(
              fontWeight: FontWeight.bold,
              color: themeColores.textoPrincipal,
            ),
          ),
          const SizedBox(height: 8),
        ],
        InkWell(
          onTap: isDisabled ? null : onTap,
          borderRadius: BorderRadius.circular(borderRadius),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: isDisabled ? themeColores.borde.withValues(alpha: 0.4) : actualFillColor,
              borderRadius: BorderRadius.circular(borderRadius),
              border: Border.all(
                color: errorText != null ? themeColores.error : Colors.transparent,
                width: errorText != null ? 1.5 : 1.0,
              ),
            ),
            child: Row(
              children: [
                if (prefixIcon != null) ...[
                  Icon(
                    prefixIcon,
                    color: isDisabled
                        ? themeColores.textoSecundario.withValues(alpha: 0.5)
                        : themeColores.textoSecundario,
                    size: 22,
                  ),
                  const SizedBox(width: 12),
                ],
                Expanded(
                  child: Text(
                    hasValue ? valueText! : hint,
                    style: hasValue
                        ? themeTextos.cuerpo.copyWith(
                            color: isDisabled
                                ? themeColores.textoSecundario.withValues(alpha: 0.6)
                                : themeColores.textoPrincipal,
                          )
                        : themeTextos.cuerpoPequeno.copyWith(
                            color: themeColores.textoSecundario.withValues(alpha: 0.8),
                          ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (hasValue && onClear != null && !isDisabled)
                  GestureDetector(
                    onTap: onClear,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: Icon(
                        Icons.close,
                        size: 18,
                        color: themeColores.textoSecundario,
                      ),
                    ),
                  ),
                if (suffixIcon != null)
                  suffixIcon!
                else
                  Icon(
                    Icons.keyboard_arrow_down,
                    color: themeColores.textoSecundario,
                    size: 22,
                  ),
              ],
            ),
          ),
        ),
        if (errorText != null) ...[
          const SizedBox(height: 4),
          Text(
            errorText!,
            style: themeTextos.cuerpoPequeno.copyWith(
              color: themeColores.error,
              fontSize: 12,
            ),
          ),
        ],
      ],
    );
  }
}
