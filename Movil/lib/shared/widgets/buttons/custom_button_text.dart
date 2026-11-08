import 'custom_button.dart';

/// Botón de Texto (Flat / Ghost): Para enlaces rápidos, acciones sutiles o botones de diálogo.
/// Sin fondo ni borde, con respuesta táctil y color de texto personalizable.
class CustomTextButton extends CustomButton {
  const CustomTextButton({
    super.key,
    required super.text,
    super.onPressed,
    super.icon,
    super.suffixIcon,
    super.isLoading = false,
    super.isDisabled = false,
    super.isSecondary = false,
    super.isDanger = false,
    super.textColor,
    super.padding,
    super.height,
    super.textStyle,
    super.iconSize = 18.0,
    super.iconSpacing = 6.0,
  }) : super(
          isText: true,
        );
}
