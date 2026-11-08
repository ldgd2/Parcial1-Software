import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../utils/ui_engine/tema.dart';

/// Input base del cual heredarán las abstracciones y variantes de campos de texto.
/// Controla la estructura visual, el tema, validación, teclados nativos móviles y estados.
class CustomInput extends StatefulWidget {
  final String hint;
  final String? label;
  final String? helperText;
  final String? errorText;
  final String? Function(String?)? validator;
  final Function(String)? onChanged;
  final Function(String)? onSubmitted;
  final Function()? onClear;
  final IconData? prefixIcon;
  final Widget? prefixWidget;
  final Widget? suffixIcon;
  final Color? fillColor;
  final TextEditingController? controller;
  final FocusNode? focusNode;
  
  // Modificadores de comportamiento y teclado
  final bool isPassword;
  final bool isSearch;
  final bool readOnly;
  final bool enabled;
  final bool autofocus;
  final VoidCallback? onTap;
  final TextInputType keyboardType;
  final TextInputAction? textInputAction;
  final int maxLines;
  final int? minLines;
  final int? maxLength;
  final List<TextInputFormatter>? inputFormatters;

  const CustomInput({
    super.key,
    required this.hint,
    this.label,
    this.helperText,
    this.errorText,
    this.validator,
    this.onChanged,
    this.onSubmitted,
    this.onClear,
    this.prefixIcon,
    this.prefixWidget,
    this.suffixIcon,
    this.fillColor,
    this.controller,
    this.focusNode,
    this.isPassword = false,
    this.isSearch = false,
    this.readOnly = false,
    this.enabled = true,
    this.autofocus = false,
    this.onTap,
    this.keyboardType = TextInputType.text,
    this.textInputAction,
    this.maxLines = 1,
    this.minLines,
    this.maxLength,
    this.inputFormatters,
  });

  @override
  State<CustomInput> createState() => _CustomInputState();
}

class _CustomInputState extends State<CustomInput> {
  late bool _obscureText;
  late TextEditingController _internalController;
  bool _tieneTexto = false;

  @override
  void initState() {
    super.initState();
    _obscureText = widget.isPassword;
    _internalController = widget.controller ?? TextEditingController();
    _tieneTexto = _internalController.text.isNotEmpty;
    _internalController.addListener(_textListener);
  }

  void _textListener() {
    final tiene = _internalController.text.isNotEmpty;
    if (tiene != _tieneTexto) {
      if (mounted) setState(() => _tieneTexto = tiene);
    }
  }

  @override
  void dispose() {
    _internalController.removeListener(_textListener);
    if (widget.controller == null) {
      _internalController.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;
    final actualFillColor = widget.fillColor ?? themeColores.fondoSecundario;

    Widget? actualSuffix = widget.suffixIcon;
    
    if (widget.isPassword) {
      actualSuffix = IconButton(
        icon: Icon(
          _obscureText ? Icons.visibility_off_outlined : Icons.visibility_outlined,
          color: themeColores.textoSecundario,
        ),
        onPressed: () => setState(() => _obscureText = !_obscureText),
      );
    } else if (widget.isSearch && _tieneTexto) {
      actualSuffix = IconButton(
        icon: Icon(Icons.close, color: themeColores.textoSecundario),
        onPressed: () {
          _internalController.clear();
          if (widget.onChanged != null) widget.onChanged!("");
          if (widget.onClear != null) widget.onClear!();
        },
      );
    }

    Widget? actualPrefix = widget.prefixWidget;
    if (actualPrefix == null && widget.prefixIcon != null) {
      actualPrefix = Icon(widget.prefixIcon, color: themeColores.textoSecundario);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (widget.label != null) ...[
          Text(
            widget.label!,
            style: themeTextos.cuerpoPequeno.copyWith(
              fontWeight: FontWeight.bold,
              color: themeColores.textoPrincipal,
            ),
          ),
          const SizedBox(height: 6),
        ],
        TextFormField(
          controller: _internalController,
          focusNode: widget.focusNode,
          obscureText: _obscureText,
          onChanged: widget.onChanged,
          onFieldSubmitted: widget.onSubmitted,
          keyboardType: widget.keyboardType,
          textInputAction: widget.textInputAction,
          maxLines: widget.isPassword ? 1 : widget.maxLines,
          minLines: widget.minLines,
          maxLength: widget.maxLength,
          style: themeTextos.cuerpo,
          readOnly: widget.readOnly,
          enabled: widget.enabled,
          autofocus: widget.autofocus,
          onTap: widget.onTap,
          validator: widget.validator,
          inputFormatters: widget.inputFormatters,
          decoration: InputDecoration(
            hintText: widget.hint,
            hintStyle: themeTextos.cuerpoPequeno.copyWith(
              color: themeColores.textoSecundario.withValues(alpha: 0.7),
            ),
            helperText: widget.helperText,
            helperStyle: themeTextos.cuerpoPequeno.copyWith(fontSize: 11),
            errorText: widget.errorText,
            errorStyle: TextStyle(color: themeColores.error, fontSize: 11),
            filled: true,
            fillColor: actualFillColor,
            prefixIcon: actualPrefix,
            suffixIcon: actualSuffix,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: themeColores.primario, width: 1.8),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: themeColores.borde.withValues(alpha: 0.5), width: 1),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: themeColores.error, width: 1.5),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: themeColores.error, width: 2),
            ),
          ),
        ),
      ],
    );
  }
}
