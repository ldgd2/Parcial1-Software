import 'custom_button.dart';

/// Botón de Peligro / Destructivo: Para acciones irreversibles (Eliminar, Cerrar sesión, etc.).
/// Utiliza el color de error del sistema por defecto.
class CustomDangerButton extends CustomButton {
  const CustomDangerButton({
    super.key,
    required super.text,
    super.onPressed,
    super.icon,
    super.suffixIcon,
    super.isLoading = false,
    super.isDisabled = false,
    super.isOutline = false,
    super.isText = false,
    super.isFullWidth = false,
    super.width,
    super.height = 48.0,
    super.borderRadius = 12.0,
    super.borderWidth = 1.5,
    super.padding,
    super.elevation = 0.0,
    super.textStyle,
    super.iconSize = 20.0,
  }) : super(
          isDanger: true,
        );
}
