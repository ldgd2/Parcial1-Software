import 'custom_button.dart';

/// Botón Secundario: Acciones complementarias o alternativas.
/// Utiliza el color secundario configurado en el tema.
class CustomSecondaryButton extends CustomButton {
  const CustomSecondaryButton({
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
  }) : super(
          isSecondary: true,
        );
}
