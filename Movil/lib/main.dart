import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'core/services/push_notification_service.dart';
import 'shared/utils/ui_engine/tema.dart';
import 'modules/auth/auth_routes.dart';
import 'modules/proyectos/proyectos_routes.dart';
import 'modules/visor/visor_routes.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await dotenv.load(fileName: ".env");
  } catch (_) {}
  await PushNotificationService.inicializar();
  runApp(const MovilVisorApp());
}

class MovilVisorApp extends StatelessWidget {
  const MovilVisorApp({super.key});

  @override
  Widget build(BuildContext context) {
    final colores = AppColores.oscuro;

    return MaterialApp(
      title: 'Visor Móvil UML',
      scaffoldMessengerKey: mensajeroGlobal,
      debugShowCheckedModeBanner: false,
      scrollBehavior: const MaterialScrollBehavior().copyWith(
        dragDevices: {
          PointerDeviceKind.mouse,
          PointerDeviceKind.touch,
          PointerDeviceKind.stylus,
          PointerDeviceKind.trackpad,
        },
      ),
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: colores.fondo,
        colorScheme: ColorScheme.dark(
          primary: colores.primario,
          secondary: colores.secundario,
          surface: colores.fondoSecundario,
          error: colores.error,
          onPrimary: colores.fondo,
          onSecondary: Colors.white,
          onSurface: colores.textoPrincipal,
          onError: Colors.white,
        ),
        appBarTheme: AppBarTheme(
          backgroundColor: colores.fondoSecundario,
          foregroundColor: colores.textoPrincipal,
          elevation: 0,
        ),
      ),
      initialRoute: AuthRoutes.login,
      routes: {
        ...AuthRoutes.routes,
        ...ProyectosRoutes.routes,
        ...VisorRoutes.routes,
      },
    );
  }
}
