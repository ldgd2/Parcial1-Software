import 'package:flutter/material.dart';
import 'views/screens/visor_screen.dart';

class VisorRoutes {
  static const String visor = '/visor';

  static Map<String, WidgetBuilder> get routes => {
        visor: (context) {
          final args = ModalRoute.of(context)?.settings.arguments as VisorArguments?;
          return VisorScreen(
            arguments: args ??
                const VisorArguments(
                  proyectoId: 0,
                  proyectoNombre: 'Visor de Diagrama',
                  codigoAcceso: '',
                ),
          );
        },
      };
}

