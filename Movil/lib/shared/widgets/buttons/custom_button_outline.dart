import 'custom_button.dart';

/// Botón con Borde (Outlined): Acciones secundarias o de menor peso visual.
/// Fondo transparente con borde y texto con el color primario (o personalizable).
class CustomOutlineButton extends CustomButton {
  const CustomOutlineButton({
    super.key,
    required super.text,
    super.onPressed,
    super.icon,
    super.suffixIcon,
    super.isLoading = false,
    super.isDisabled = false,
    super.isSecondary = false,
    super.isFullWidth = false,
    super.width,
    super.height = 48.0,
    super.borderRadius = 12.0,
    super.borderWidth = 1.5,
    super.borderColor,
    super.textColor,
    super.padding,
    super.textStyle,
    super.iconSize = 20.0,
  }) : super(
          isOutline: true,
        );
}
