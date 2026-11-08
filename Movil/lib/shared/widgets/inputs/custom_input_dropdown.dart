import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

class CustomDropdownInput<T> extends StatefulWidget {
  final String hint;
  final String? label;
  
  /// El valor seleccionado explícitamente (si no se usa controller).
  final T? value;
  
  /// Controlador opcional para leer/escribir el valor (ideal si usas Formularios genéricos).
  final TextEditingController? controller;
  
  /// Mapa abstracto de opciones: { valor_interno: "Texto Visible" }
  /// Ej: {'M': 'Masculino', 'F': 'Femenino'}
  final Map<T, String> options;
  
  final Function(T?)? onChanged;
  final IconData? prefixIcon;
  final Color? fillColor;
  final String? errorText;
  final String? Function(T?)? validator;

  const CustomDropdownInput({
    super.key,
    required this.hint,
    required this.options,
    this.value,
    this.controller,
    this.label,
    this.onChanged,
    this.prefixIcon,
    this.fillColor,
    this.errorText,
    this.validator,
  });

  @override
  State<CustomDropdownInput<T>> createState() => _CustomDropdownInputState<T>();
}

class _CustomDropdownInputState<T> extends State<CustomDropdownInput<T>> {
  T? _currentValue;

  @override
  void initState() {
    super.initState();
    _initializeValue();
  }

  void _initializeValue() {
    _currentValue = widget.value;
    
    // Si no hay value pero hay un controller con texto, intentar inicializar desde el controller
    if (_currentValue == null && widget.controller != null && widget.controller!.text.isNotEmpty) {
      if (T == String) {
        _currentValue = widget.controller!.text as T;
      }
    }
  }
  
  @override
  void didUpdateWidget(CustomDropdownInput<T> oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.value != oldWidget.value) {
      _currentValue = widget.value;
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;
    final actualFillColor = widget.fillColor ?? themeColores.borde.withValues(alpha: 0.3);

    // Abstracción mágica: Convertir el mapa "options" en DropdownMenuItems
    final List<DropdownMenuItem<T>> dropdownItems = widget.options.entries.map((entry) {
      return DropdownMenuItem<T>(
        value: entry.key,
        child: Text(entry.value),
      );
    }).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (widget.label != null) ...[
          Text(
            widget.label!,
            style: themeTextos.cuerpoPequeno.copyWith(fontWeight: FontWeight.bold, color: themeColores.textoPrincipal),
          ),
          const SizedBox(height: 8),
        ],
        DropdownButtonFormField<T>(
          value: _currentValue,
          items: dropdownItems,
          validator: widget.validator,
          onChanged: (newValue) {
            setState(() {
              _currentValue = newValue;
            });
            
            // Sincronizar con el controller automáticamente si se proporcionó uno
            if (widget.controller != null) {
              widget.controller!.text = newValue?.toString() ?? '';
            }
            
            // Disparar el callback externo
            if (widget.onChanged != null) {
              widget.onChanged!(newValue);
            }
          },
          style: themeTextos.cuerpo.copyWith(color: themeColores.textoPrincipal),
          dropdownColor: themeColores.fondoSecundario,
          icon: Icon(Icons.keyboard_arrow_down, color: themeColores.textoSecundario),
          decoration: InputDecoration(
            hintText: widget.hint,
            hintStyle: themeTextos.cuerpoPequeno,
            filled: true,
            fillColor: actualFillColor,
            errorText: widget.errorText,
            prefixIcon: widget.prefixIcon != null ? Icon(widget.prefixIcon, color: themeColores.textoSecundario) : null,
            contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: themeColores.primario, width: 2),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: Colors.transparent, width: 1),
            ),
          ),
        ),
      ],
    );
  }
}
