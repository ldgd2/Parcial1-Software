import 'dart:ui';
import 'package:flutter/material.dart';
import '../../widgets/dismissible/custom_dismissible.dart';
import '../../widgets/dismissible/custom_dismissible_background.dart';

extension ModificadoresResponsivos on Widget {
  // 1. Proporciones (Ej: .ancho(0.5) ocupa exactamente la mitad de la pantalla/padre)
  Widget ancho(double porcentaje) => FractionallySizedBox(widthFactor: porcentaje, child: this);
  Widget alto(double porcentaje) => FractionallySizedBox(heightFactor: porcentaje, child: this);
  
  // 2. Límites Máximos (Crucial para Tablets: evita que un input se estire de borde a borde)
  Widget maxAncho(double max) => ConstrainedBox(constraints: BoxConstraints(maxWidth: max), child: this);
  Widget maxAlto(double max) => ConstrainedBox(constraints: BoxConstraints(maxHeight: max), child: this);
  
  // 3. Aspect Ratio perfecto (Ej: 16:9 para un reproductor de video sin importar la pantalla)
  Widget proporcion(double ratio) => AspectRatio(aspectRatio: ratio, child: this);
  
  // 4. Flexibilidad dinámica
  Widget expandir({int flex = 1}) => Expanded(flex: flex, child: this);

  Widget w(double ancho) => SizedBox(width: ancho, child: this);
  Widget h(double alto) => SizedBox(height: alto, child: this);
  Widget centrar() => Center(child: this);
  
  Widget pad(double padding) => Padding(padding: EdgeInsets.all(padding), child: this);
  Widget padXY(double x, double y) => Padding(padding: EdgeInsets.symmetric(horizontal: x, vertical: y), child: this);
  Widget padSolo({double l = 0, double t = 0, double r = 0, double b = 0}) => Padding(padding: EdgeInsets.only(left: l, top: t, right: r, bottom: b), child: this);
  
  Widget pos({double? x, double? y, double? l, double? r, double? t, double? b}) {
    if (x != null || y != null) {
      return Transform.translate(offset: Offset(x ?? 0, y ?? 0), child: this);
    }
    return Padding(padding: EdgeInsets.only(left: l ?? 0, right: r ?? 0, top: t ?? 0, bottom: b ?? 0), child: this);
  }

  Widget ocultar(bool condicion) => condicion ? const SizedBox.shrink() : this;
  Widget mostrar(bool condicion) => condicion ? this : const SizedBox.shrink();

  Widget click(VoidCallback accion) => GestureDetector(onTap: accion, child: this);
  Widget scroll() => SingleChildScrollView(physics: const BouncingScrollPhysics(), child: this);
  
  Widget sombra({double difuminado = 5, Color color = Colors.black12, Offset offset = const Offset(0, 5)}) {
    return Container(
      decoration: BoxDecoration(
        boxShadow: [
          BoxShadow(color: color, blurRadius: difuminado, offset: offset)
        ],
      ),
      child: this,
    );
  }

  // 5. Transformaciones y visuales base
  Widget fondo(Color color) => ColoredBox(color: color, child: this);
  Widget opacidad(double valor) => Opacity(opacity: valor, child: this);
  Widget rotar(double angulo) => Transform.rotate(angle: angulo, child: this);
  Widget escalar(double escala) => Transform.scale(scale: escala, child: this);
  Widget alinear([AlignmentGeometry alineacion = Alignment.center]) => Align(alignment: alineacion, child: this);
  
  Widget clip({double radio = 0, bool ovalado = false}) {
    if (ovalado) return ClipOval(child: this);
    return ClipRRect(borderRadius: BorderRadius.circular(radio), child: this);
  }

  // =======================================================
  // MAGIA NEGRA: REACTIVIDAD ABSTRACTA
  // =======================================================
  /// Envuelve cualquier Widget en un entorno reactivo para actualizar su estado interno
  /// sin necesidad de crear un StatefulWidget completo.
  /// Ideal para contadores, toggles o componentes interactivos aislados.
  Widget reactivo(Widget Function(BuildContext context, void Function(void Function()) setState) builder) {
    return StatefulBuilder(
      builder: (context, setState) {
        return builder(context, setState);
      },
    );
  }
}

extension EstilosAvanzados on Widget {
  // El modificador definitivo para transformar la apariencia
  Widget estilo({
    Color? bg, 
    double radio = 0, 
    bool circulo = false,
    Color? bordeColor, 
    double bordeGrosor = 1,
    bool sombra = false,
    Gradient? gradiente,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: gradiente == null ? bg : null,
        gradient: gradiente,
        shape: circulo ? BoxShape.circle : BoxShape.rectangle,
        borderRadius: circulo ? null : BorderRadius.circular(radio),
        border: bordeColor != null ? Border.all(color: bordeColor, width: bordeGrosor) : null,
        boxShadow: sombra ? [
          BoxShadow(color: Colors.black.withValues(alpha: 0.1), blurRadius: 15, offset: const Offset(0, 5))
        ] : null,
      ),
      clipBehavior: Clip.antiAlias, // Evita que los hijos se salgan de los bordes redondeados
      child: this,
    );
  }

  // Efecto Glassmorphism (Cristal difuminado) súper avanzado
  Widget cristal({double desenfoque = 10, double opacidad = 0.1}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(15),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: desenfoque, sigmaY: desenfoque),
        child: Container(
          color: Colors.white.withValues(alpha: opacidad),
          child: this,
        ),
      ),
    );
  }

  Widget borde(Color color, {double radio = 0, double grosor = 1}) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radio),
        border: Border.all(color: color, width: grosor),
      ),
      child: this,
    );
  }

  /// Convierte cualquier Widget (Tarjetas, Filas, Contenedores) en Deslizable (Swipe-to-Dismiss / Gmail style)
  Widget deslizable({
    required Key key,
    VoidCallback? onEliminar,
    VoidCallback? onArchivar,
    Future<bool?> Function(DismissDirection)? confirmar,
    double radioBorde = 16.0,
    Widget? fondoIzquierda,
    Widget? fondoDerecha,
  }) {
    return CustomDismissible(
      dismissKey: key,
      borderRadius: radioBorde,
      background: fondoIzquierda ?? CustomDismissibleBackground.archive(borderRadius: radioBorde),
      secondaryBackground: fondoDerecha ?? CustomDismissibleBackground.delete(borderRadius: radioBorde),
      confirmDismiss: confirmar,
      onSwipeLeft: onEliminar,
      onSwipeRight: onArchivar,
      child: this,
    );
  }

  /// Convierte cualquier Widget en Deslizable para Aceptar o Rechazar (Estándar Universal de Decisiones)
  /// Deslizar a la Derecha = Aceptar (Verde)
  /// Deslizar a la Izquierda = Rechazar / Descartar (Rojo)
  Widget deslizableDecision({
    required Key key,
    VoidCallback? onAceptar,
    VoidCallback? onRechazar,
    String textoAceptar = "Aceptar",
    String textoRechazar = "Rechazar",
    Future<bool?> Function(DismissDirection)? confirmar,
    double radioBorde = 16.0,
  }) {
    return CustomDismissible.decision(
      key: key,
      onAccept: onAceptar,
      onReject: onRechazar,
      acceptLabel: textoAceptar,
      rejectLabel: textoRechazar,
      confirmDismiss: confirmar,
      borderRadius: radioBorde,
      child: this,
    );
  }
}

// =======================================================
// COMPONENTES REACTIVOS DEL SISTEMA DE DISEÑO
// =======================================================

/// Abstracción para aislar el re-dibujado de estado local sin exponer StatefulBuilder.
/// Facilita una sintaxis 100% declarativa en las vistas de la aplicación.
class CustomRebuilder extends StatefulWidget {
  final Widget Function(void Function(VoidCallback fn) actualizar) builder;

  const CustomRebuilder({super.key, required this.builder});

  @override
  State<CustomRebuilder> createState() => _CustomRebuilderState();
}

class _CustomRebuilderState extends State<CustomRebuilder> {
  @override
  Widget build(BuildContext context) {
    return widget.builder(setState);
  }
}
