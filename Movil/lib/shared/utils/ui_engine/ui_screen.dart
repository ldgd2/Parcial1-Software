import 'package:flutter/material.dart';
import 'tema.dart';
import 'list_modifiers.dart';

enum PosicionBotonFlotante {
  centro,
  derecha,
  izquierda,
}

/// Lienzo y Andamiaje Base (`UIScreen`):
/// Abstracción centralizada para la creación de pantallas móviles.
/// Permite definir todos los atributos del andamiaje (título, navegación, FAB, capas flotantes/overlays, padding, scroll, centrado)
/// de forma cohesiva en el constructor o como lienzo declarativo.
class UIScreen extends StatelessWidget {
  final String? titulo;
  final Color? bgColor;
  final bool conScroll;
  final bool centrado;
  final bool conSafeArea;
  final double paddingX;
  final double paddingY;
  final bool resizeToAvoidBottomInset;
  final PreferredSizeWidget? appBar;
  final List<Widget>? accionesAppBar;
  final Widget? botonFlotante;
  final PosicionBotonFlotante? posicionBotonFlotante;
  final Widget? bottomNavigationBar;
  final Widget? drawer;
  final List<Widget>? capasFlotantes;
  final List<Widget> Function(BuildContext context)? cuerpo;
  final Widget Function(BuildContext context)? builder;

  const UIScreen({
    super.key,
    this.titulo,
    this.bgColor,
    this.conScroll = true,
    this.centrado = false,
    this.conSafeArea = true,
    this.paddingX = 16.0,
    this.paddingY = 16.0,
    this.resizeToAvoidBottomInset = true,
    this.appBar,
    this.accionesAppBar,
    this.botonFlotante,
    this.posicionBotonFlotante,
    this.bottomNavigationBar,
    this.drawer,
    this.capasFlotantes,
    this.cuerpo,
    this.builder,
  });

  // =======================================================
  // CONTENIDO (Sobrescribible o inyectable vía constructor)
  // =======================================================
  Widget contenido(BuildContext context) {
    if (cuerpo != null) {
      return cuerpo!(context).columna();
    }
    if (builder != null) {
      return builder!(context);
    }
    return const SizedBox.shrink();
  }

  // =======================================================
  // MOTOR DE RENDERIZADO DEL ANDAMIAJE (SCAFFOLD)
  // =======================================================
  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    // 1. Obtenemos el contenido del lienzo
    Widget widgetCuerpo = contenido(context);

    // 2. Centrado automático
    if (centrado) {
      widgetCuerpo = Center(child: widgetCuerpo);
    }

    // 3. Scroll con física suave
    if (conScroll) {
      widgetCuerpo = SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        child: widgetCuerpo,
      );
    }

    // 4. Espaciado global (Padding abstracto)
    widgetCuerpo = Padding(
      padding: EdgeInsets.symmetric(horizontal: paddingX, vertical: paddingY),
      child: widgetCuerpo,
    );

    // 5. Área segura (SafeArea)
    if (conSafeArea) {
      widgetCuerpo = SafeArea(child: widgetCuerpo);
    }

    // 6. Si existen capas flotantes (overlays) que siguen la pantalla sobre el contenido
    if (capasFlotantes != null && capasFlotantes!.isNotEmpty) {
      widgetCuerpo = Stack(
        fit: StackFit.expand,
        children: [
          widgetCuerpo,
          ...capasFlotantes!,
        ],
      );
    }

    // 7. Barra superior (AppBar)
    PreferredSizeWidget? finalAppBar = appBar;
    final String? screenTitle = titulo;

    if (finalAppBar == null && screenTitle != null && screenTitle.isNotEmpty) {
      finalAppBar = AppBar(
        title: Text(
          screenTitle,
          style: themeTextos.titulo.copyWith(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: themeColores.primario,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: accionesAppBar,
      );
    }

    FloatingActionButtonLocation location = FloatingActionButtonLocation.endFloat;
    if (posicionBotonFlotante == PosicionBotonFlotante.centro) {
      location = FloatingActionButtonLocation.centerDocked;
    } else if (posicionBotonFlotante == PosicionBotonFlotante.izquierda) {
      location = FloatingActionButtonLocation.startFloat;
    }

    return Scaffold(
      backgroundColor: bgColor ?? themeColores.fondo,
      appBar: finalAppBar,
      body: widgetCuerpo,
      drawer: drawer,
      floatingActionButton: botonFlotante,
      floatingActionButtonLocation: location,
      bottomNavigationBar: bottomNavigationBar,
      resizeToAvoidBottomInset: resizeToAvoidBottomInset,
    );
  }
}
