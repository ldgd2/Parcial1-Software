import 'package:flutter/material.dart';
import 'views/screens/proyectos_screen.dart';

class ProyectosRoutes {
  static const String proyectos = '/proyectos';

  static Map<String, WidgetBuilder> get routes => {
        proyectos: (context) => const ProyectosScreen(),
      };
}

