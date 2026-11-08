import 'package:flutter/material.dart';
import 'custom_switch.dart';

/// Switch Asíncrono (`CustomAsyncSwitch`):
/// Ideal para configuraciones que se sincronizan con una API / Base de datos.
/// Muestra un indicador de carga automático mientras se resuelve el `Future` de la petición.
class CustomAsyncSwitch extends StatefulWidget {
  final bool initialValue;
  final Future<bool> Function(bool newValue)? onAsyncChanged;
  final Color? activeColor;
  final bool isDisabled;
  final IconData? activeIcon;
  final IconData? inactiveIcon;

  const CustomAsyncSwitch({
    super.key,
    required this.initialValue,
    required this.onAsyncChanged,
    this.activeColor,
    this.isDisabled = false,
    this.activeIcon,
    this.inactiveIcon,
  });

  @override
  State<CustomAsyncSwitch> createState() => _CustomAsyncSwitchState();
}

class _CustomAsyncSwitchState extends State<CustomAsyncSwitch> {
  late bool _currentValue;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _currentValue = widget.initialValue;
  }

  @override
  void didUpdateWidget(covariant CustomAsyncSwitch oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialValue != widget.initialValue) {
      _currentValue = widget.initialValue;
    }
  }

  Future<void> _handleToggle(bool newValue) async {
    if (_isLoading || widget.isDisabled || widget.onAsyncChanged == null) return;

    setState(() => _isLoading = true);

    try {
      final success = await widget.onAsyncChanged!(newValue);
      if (mounted) {
        setState(() {
          if (success) {
            _currentValue = newValue;
          }
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return CustomSwitch(
      value: _currentValue,
      onChanged: _handleToggle,
      isLoading: _isLoading,
      isDisabled: widget.isDisabled,
      activeColor: widget.activeColor,
      activeIcon: widget.activeIcon,
      inactiveIcon: widget.inactiveIcon,
    );
  }
}
