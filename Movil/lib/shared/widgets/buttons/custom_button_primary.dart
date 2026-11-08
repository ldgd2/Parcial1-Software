import 'custom_button.dart';

/// Botón Primario: Acción principal de una pantalla o formulario.
/// Utiliza el color primario del tema con texto e icono en blanco.
class CustomPrimaryButton extends CustomButton {
  const CustomPrimaryButton({
    super.key,
    required super.text,
    super.onPressed,
    super.icon,
    super.suffixIcon,
    super.isLoading = false,
    super.isDisabled = false,
    super.isFullWidth = false,
    super.width,
    super.height = 48.0,
    super.borderRadius = 12.0,
    super.padding,
    super.elevation = 0.0,
    super.backgroundColor,
    super.textColor,
    super.textStyle,
    super.iconSize = 20.0,
  });
}
