import 'package:flutter/material.dart';
import 'tema.dart';
import 'ui_screen.dart';

// Este es el Dispensador Factory
class UI {
  @Deprecated('Usa CustomTextField, CustomPasswordField o CustomSearchField de shared/widgets/inputs en su lugar.')
  // 1. Mapeas el Input
  static Widget input(
    String hint, 
    Function(String) accion, {
    bool clave = false,
    TextInputType teclado = TextInputType.text,
    int maxLineas = 1,
    IconData? icono,
    Color? fillColor,
  }) {
    return TextField(
      obscureText: clave,
      onChanged: accion,
      keyboardType: teclado,
      maxLines: clave ? 1 : maxLineas,
      style: AppTheme.textos.cuerpo,
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: AppTheme.textos.cuerpoPequeno,
        filled: true,
        fillColor: fillColor ?? AppTheme.colores.borde.withOpacity(0.3),
        prefixIcon: icono != null ? Icon(icono, color: AppTheme.colores.textoSecundario) : null,
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.colores.primario, width: 2),
        ),
      ),
    );
  }

  @Deprecated('Usa CustomPrimaryButton, CustomSecondaryButton, CustomOutlineButton, etc. de shared/widgets/buttons en su lugar.')
  // 2. Mapeas el Botón
  static Widget boton(
    String texto, 
    VoidCallback accion, {
    Color? bgColor,
    Color? textColor,
    double radius = 12,
    bool outline = false,
    IconData? icono,
  }) {
    final shape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(radius));
    final padding = const EdgeInsets.symmetric(vertical: 15, horizontal: 20);
    final colorFondo = bgColor ?? AppTheme.colores.primario;
    final colorTexto = textColor ?? Colors.white;

    if (outline) {
      return OutlinedButton.icon(
        onPressed: accion,
        icon: icono != null ? Icon(icono) : const SizedBox.shrink(),
        label: Text(texto, style: AppTheme.textos.boton.copyWith(color: textColor ?? colorFondo)),
        style: OutlinedButton.styleFrom(
          shape: shape,
          padding: padding,
          foregroundColor: textColor ?? colorFondo,
          side: BorderSide(color: colorFondo),
        ),
      );
    }

    if (icono != null) {
      return ElevatedButton.icon(
        onPressed: accion,
        icon: Icon(icono),
        label: Text(texto, style: AppTheme.textos.boton.copyWith(color: colorTexto)),
        style: ElevatedButton.styleFrom(
          shape: shape,
          padding: padding,
          backgroundColor: colorFondo,
          foregroundColor: colorTexto,
        ),
      );
    }

    return ElevatedButton(
      onPressed: accion,
      style: ElevatedButton.styleFrom(
        shape: shape,
        padding: padding,
        backgroundColor: colorFondo,
        foregroundColor: colorTexto,
      ),
      child: Text(texto, style: AppTheme.textos.boton.copyWith(color: colorTexto)),
    );
  }

  // 3. Mapeas un loader
  static Widget loader({Color? color, double strokeWidth = 4.0}) => CircularProgressIndicator(color: color ?? AppTheme.colores.primario, strokeWidth: strokeWidth);

  /// 4. Lienzo / Pantalla Declarativa Rápida (Canvas Builder)
  static Widget lienzo({
    String? titulo,
    bool centrado = false,
    bool conScroll = true,
    bool conSafeArea = true,
    Color? bgColor,
    double paddingX = 16.0,
    double paddingY = 16.0,
    List<Widget>? accionesAppBar,
    Widget? floatingActionButton,
    Widget? bottomNavigationBar,
    required List<Widget> Function(BuildContext context) cuerpo,
  }) {
    return UIScreen(
      titulo: titulo,
      centrado: centrado,
      conScroll: conScroll,
      conSafeArea: conSafeArea,
      bgColor: bgColor,
      paddingX: paddingX,
      paddingY: paddingY,
      accionesAppBar: accionesAppBar,
      botonFlotante: floatingActionButton,
      bottomNavigationBar: bottomNavigationBar,
      cuerpo: cuerpo,
    );
  }
}
