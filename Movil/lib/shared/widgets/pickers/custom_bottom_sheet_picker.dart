import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_picker_field.dart';

/// Elemento para el selector de opciones táctil
class PickerItem<T> {
  final T value;
  final String label;
  final String? subtitle;
  final IconData? icon;

  const PickerItem({
    required this.value,
    required this.label,
    this.subtitle,
    this.icon,
  });
}

/// Selector de Opciones en Hoja Inferior (`CustomBottomSheetPicker<T>`).
/// Reemplazo moderno y optimizado para móviles frente a los menús desplegables clásicos.
/// Despliega un modal inferior con soporte para búsqueda en vivo, iconos y selección táctil clara.
class CustomBottomSheetPicker<T> extends StatefulWidget {
  final String hint;
  final String? label;
  final String? sheetTitle;
  final T? value;
  final List<PickerItem<T>> items;
  final ValueChanged<T>? onItemSelected;
  final VoidCallback? onClear;
  final IconData? prefixIcon;
  final Color? fillColor;
  final bool isDisabled;
  final bool isSearchable;
  final String? errorText;

  const CustomBottomSheetPicker({
    super.key,
    required this.hint,
    required this.items,
    this.label,
    this.sheetTitle,
    this.value,
    this.onItemSelected,
    this.onClear,
    this.prefixIcon,
    this.fillColor,
    this.isDisabled = false,
    this.isSearchable = false,
    this.errorText,
  });

  @override
  State<CustomBottomSheetPicker<T>> createState() => _CustomBottomSheetPickerState<T>();
}

class _CustomBottomSheetPickerState<T> extends State<CustomBottomSheetPicker<T>> {
  T? _selectedValue;

  @override
  void initState() {
    super.initState();
    _selectedValue = widget.value;
  }

  @override
  void didUpdateWidget(covariant CustomBottomSheetPicker<T> oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _selectedValue = widget.value;
    }
  }

  String? _getDisplayText() {
    if (_selectedValue == null) return null;
    final found = widget.items.where((i) => i.value == _selectedValue);
    if (found.isNotEmpty) {
      return found.first.label;
    }
    return null;
  }

  void _showBottomSheet(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: themeColores.fondoSecundario,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        return _BottomSheetContent<T>(
          title: widget.sheetTitle ?? widget.label ?? widget.hint,
          items: widget.items,
          selectedValue: _selectedValue,
          isSearchable: widget.isSearchable,
          onSelected: (selectedItem) {
            setState(() => _selectedValue = selectedItem.value);
            widget.onItemSelected?.call(selectedItem.value);
            Navigator.of(ctx).pop();
          },
          themeColores: themeColores,
          themeTextos: themeTextos,
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return CustomPickerField(
      hint: widget.hint,
      label: widget.label,
      valueText: _getDisplayText(),
      prefixIcon: widget.prefixIcon,
      fillColor: widget.fillColor,
      isDisabled: widget.isDisabled,
      errorText: widget.errorText,
      onTap: () => _showBottomSheet(context),
      onClear: widget.onClear != null
          ? () {
              setState(() => _selectedValue = null);
              widget.onClear!();
            }
          : null,
    );
  }
}

class _BottomSheetContent<T> extends StatefulWidget {
  final String title;
  final List<PickerItem<T>> items;
  final T? selectedValue;
  final bool isSearchable;
  final ValueChanged<PickerItem<T>> onSelected;
  final AppColores themeColores;
  final AppTextos themeTextos;

  const _BottomSheetContent({
    required this.title,
    required this.items,
    required this.selectedValue,
    required this.isSearchable,
    required this.onSelected,
    required this.themeColores,
    required this.themeTextos,
  });

  @override
  State<_BottomSheetContent<T>> createState() => _BottomSheetContentState<T>();
}

class _BottomSheetContentState<T> extends State<_BottomSheetContent<T>> {
  late List<PickerItem<T>> _filteredItems;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _filteredItems = widget.items;
    _searchController.addListener(_onSearchChanged);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged() {
    final query = _searchController.text.toLowerCase();
    setState(() {
      if (query.isEmpty) {
        _filteredItems = widget.items;
      } else {
        _filteredItems = widget.items.where((item) {
          final labelMatch = item.label.toLowerCase().contains(query);
          final subtitleMatch = item.subtitle?.toLowerCase().contains(query) ?? false;
          return labelMatch || subtitleMatch;
        }).toList();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final maxHeight = mediaQuery.size.height * 0.75;

    return Container(
      constraints: BoxConstraints(maxHeight: maxHeight),
      padding: EdgeInsets.only(
        bottom: mediaQuery.viewInsets.bottom + 16,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Barra de agarre superior (Handle indicator)
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 12, bottom: 8),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: widget.themeColores.borde,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          // Título de la cabecera
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    widget.title,
                    style: widget.themeTextos.subtitulo.copyWith(
                      color: widget.themeColores.textoPrincipal,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                IconButton(
                  icon: Icon(Icons.close, color: widget.themeColores.textoSecundario),
                  onPressed: () => Navigator.of(context).pop(),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
          ),

          // Buscador opcional
          if (widget.isSearchable)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: TextField(
                controller: _searchController,
                style: widget.themeTextos.cuerpo,
                decoration: InputDecoration(
                  hintText: "Buscar opción...",
                  hintStyle: widget.themeTextos.cuerpoPequeno,
                  prefixIcon: Icon(Icons.search, color: widget.themeColores.textoSecundario),
                  filled: true,
                  fillColor: widget.themeColores.fondo,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
            ),

          const Divider(height: 1),

          // Lista de opciones táctiles
          Flexible(
            child: _filteredItems.isEmpty
                ? Padding(
                    padding: const EdgeInsets.all(32),
                    child: Text(
                      "No se encontraron resultados",
                      style: widget.themeTextos.cuerpoPequeno,
                    ),
                  )
                : ListView.separated(
                    shrinkWrap: true,
                    itemCount: _filteredItems.length,
                    separatorBuilder: (context, index) => Divider(
                      height: 1,
                      indent: 16,
                      endIndent: 16,
                      color: widget.themeColores.borde.withValues(alpha: 0.5),
                    ),
                    itemBuilder: (ctx, index) {
                      final item = _filteredItems[index];
                      final bool isSelected = item.value == widget.selectedValue;

                      return InkWell(
                        onTap: () => widget.onSelected(item),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                          color: isSelected
                              ? widget.themeColores.primario.withValues(alpha: 0.08)
                              : Colors.transparent,
                          child: Row(
                            children: [
                              if (item.icon != null) ...[
                                Icon(
                                  item.icon,
                                  color: isSelected
                                      ? widget.themeColores.primario
                                      : widget.themeColores.textoSecundario,
                                  size: 22,
                                ),
                                const SizedBox(width: 14),
                              ],
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      item.label,
                                      style: widget.themeTextos.cuerpo.copyWith(
                                        color: isSelected
                                            ? widget.themeColores.primario
                                            : widget.themeColores.textoPrincipal,
                                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                      ),
                                    ),
                                    if (item.subtitle != null) ...[
                                      const SizedBox(height: 2),
                                      Text(
                                        item.subtitle!,
                                        style: widget.themeTextos.cuerpoPequeno.copyWith(
                                          color: widget.themeColores.textoSecundario,
                                          fontSize: 12,
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                              if (isSelected)
                                Icon(
                                  Icons.check_circle,
                                  color: widget.themeColores.primario,
                                  size: 22,
                                ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
