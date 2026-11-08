import 'package:flutter/material.dart';

/// Envoltorio (Wrapper) que otorga capacidades de zoom y paneo (Pinch-to-zoom)
/// a cualquier widget, idealmente imágenes o diagramas complejos.
class CustomInteractiveViewer extends StatelessWidget {
  final Widget contenido;
  final double minScale;
  final double maxScale;
  final bool panEnabled;
  final bool scaleEnabled;
  final TransformationController? controller;

  const CustomInteractiveViewer({
    super.key,
    required this.contenido,
    this.minScale = 1.0,
    this.maxScale = 4.0,
    this.panEnabled = true,
    this.scaleEnabled = true,
    this.controller,
  });

  /// Abstracción para inicializar con un icono rápidamente sin preocuparse del Widget
  factory CustomInteractiveViewer.icono({
    required IconData icono, 
    double size = 150, 
    Color color = Colors.grey,
  }) {
    return CustomInteractiveViewer(
      contenido: Icon(icono, size: size, color: color),
    );
  }

  /// Abstracción para mostrar una imagen desde la red fácilmente
  factory CustomInteractiveViewer.imagenEnRed({
    required String url,
  }) {
    return CustomInteractiveViewer(
      contenido: Image.network(url, fit: BoxFit.contain),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Si no se provee un controlador, InteractiveViewer usa uno interno.
    // Usamos LayoutBuilder para asegurarnos de que ocupa el espacio adecuadamente
    // si se coloca dentro de contenedores flexibles.
    return LayoutBuilder(
      builder: (context, constraints) {
        return ClipRRect(
          child: InteractiveViewer(
            transformationController: controller,
            minScale: minScale,
            maxScale: maxScale,
            panEnabled: panEnabled,
            scaleEnabled: scaleEnabled,
            // boundaryMargin es necesario si queremos que la imagen pueda 
            // hacerse más pequeña que el viewport, pero usualmente no es el caso.
            boundaryMargin: EdgeInsets.zero,
            // Centra automáticamente el contenido
            constrained: true,
            child: SizedBox(
              width: constraints.maxWidth,
              height: constraints.maxHeight,
              child: Center(child: contenido),
            ),
          ),
        );
      },
    );
  }
}
