import 'package:flutter/material.dart';
import 'custom_slider.dart';

/// Slider con Iconos Flanqueados (`CustomIconSlider`):
/// Optimizado para ajustes de hardware y multimedia en móvil (Volumen, Brillo, Zoom, Tamaño de Texto).
class CustomIconSlider extends CustomSlider {
  const CustomIconSlider({
    super.key,
    required super.value,
    required super.onChanged,
    super.onChangeEnd,
    super.min = 0.0,
    super.max = 100.0,
    super.divisions,
    super.headerTitle,
    super.label,
    super.valueFormatter,
    super.showValueIndicator = false,
    required IconData prefixIcon,
    required IconData suffixIcon,
    super.activeColor,
    super.inactiveColor,
    super.thumbColor,
    super.isDisabled = false,
    super.trackHeight = 6.0,
  }) : super(
          prefixIcon: prefixIcon,
          suffixIcon: suffixIcon,
        );

  /// Constructor predefinido para Volumen (Mute 🔈 → Max 🔊)
  factory CustomIconSlider.volumen({
    Key? key,
    required double value,
    required ValueChanged<double>? onChanged,
    String? headerTitle = "Volumen",
    bool isDisabled = false,
  }) {
    return CustomIconSlider(
      key: key,
      value: value,
      min: 0.0,
      max: 100.0,
      onChanged: onChanged,
      headerTitle: headerTitle,
      showValueIndicator: true,
      valueFormatter: (val) => "${val.toInt()}%",
      prefixIcon: value == 0 ? Icons.volume_mute_outlined : Icons.volume_down_outlined,
      suffixIcon: Icons.volume_up_outlined,
      isDisabled: isDisabled,
    );
  }

  /// Constructor predefinido para Brillo de Pantalla (Bajo 🔅 → Alto 🔆)
  factory CustomIconSlider.brillo({
    Key? key,
    required double value,
    required ValueChanged<double>? onChanged,
    String? headerTitle = "Brillo de pantalla",
    bool isDisabled = false,
  }) {
    return CustomIconSlider(
      key: key,
      value: value,
      min: 0.0,
      max: 100.0,
      onChanged: onChanged,
      headerTitle: headerTitle,
      showValueIndicator: true,
      valueFormatter: (val) => "${val.toInt()}%",
      prefixIcon: Icons.brightness_low_outlined,
      suffixIcon: Icons.brightness_high_outlined,
      activeColor: const Color(0xFFF59E0B), // Ámbar brillante
      isDisabled: isDisabled,
    );
  }

  /// Constructor predefinido para Zoom / Escala (Alejar 🔍➖ → Acercar 🔍➕)
  factory CustomIconSlider.zoom({
    Key? key,
    required double value,
    required ValueChanged<double>? onChanged,
    String? headerTitle = "Nivel de Zoom",
    bool isDisabled = false,
  }) {
    return CustomIconSlider(
      key: key,
      value: value,
      min: 1.0,
      max: 10.0,
      divisions: 9,
      onChanged: onChanged,
      headerTitle: headerTitle,
      showValueIndicator: true,
      valueFormatter: (val) => "${val.toStringAsFixed(1)}x",
      prefixIcon: Icons.zoom_out_outlined,
      suffixIcon: Icons.zoom_in_outlined,
      isDisabled: isDisabled,
    );
  }
}
