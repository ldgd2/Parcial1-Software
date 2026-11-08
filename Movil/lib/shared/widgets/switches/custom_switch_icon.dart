import 'package:flutter/material.dart';
import 'custom_switch.dart';

/// Switch con Iconos Internos (`CustomIconSwitch`):
/// Muestra iconos representativos en la perilla móvil (Thumb), ideal para cambio de tema (Sol/Luna),
/// notificaciones (Campana/Mute) o privacidad/bloqueo (Candado).
class CustomIconSwitch extends CustomSwitch {
  const CustomIconSwitch({
    super.key,
    required super.value,
    required super.onChanged,
    super.activeColor,
    super.activeTrackColor,
    super.inactiveThumbColor,
    super.inactiveTrackColor,
    super.isDisabled = false,
    super.isLoading = false,
    super.scale = 1.0,
    required IconData activeIcon,
    required IconData inactiveIcon,
  }) : super(
          activeIcon: activeIcon,
          inactiveIcon: inactiveIcon,
        );

  /// Constructor fábrica para alternar Modo Oscuro / Claro
  factory CustomIconSwitch.tema({
    Key? key,
    required bool esOscuro,
    required ValueChanged<bool>? onChanged,
    bool isDisabled = false,
    bool isLoading = false,
  }) {
    return CustomIconSwitch(
      key: key,
      value: esOscuro,
      onChanged: onChanged,
      activeIcon: Icons.nightlight_round,
      inactiveIcon: Icons.wb_sunny_rounded,
      activeColor: const Color(0xFF6366F1), // Índigo nocturno
      isDisabled: isDisabled,
      isLoading: isLoading,
    );
  }

  /// Constructor fábrica para alternar Notificaciones (Sonido/Mute)
  factory CustomIconSwitch.notificaciones({
    Key? key,
    required bool activadas,
    required ValueChanged<bool>? onChanged,
    bool isDisabled = false,
    bool isLoading = false,
  }) {
    return CustomIconSwitch(
      key: key,
      value: activadas,
      onChanged: onChanged,
      activeIcon: Icons.notifications_active_outlined,
      inactiveIcon: Icons.notifications_off_outlined,
      isDisabled: isDisabled,
      isLoading: isLoading,
    );
  }
}
