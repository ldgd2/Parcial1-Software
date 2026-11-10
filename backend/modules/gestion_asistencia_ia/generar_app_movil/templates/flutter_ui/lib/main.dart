import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:intl/date_symbol_data_local.dart';

import 'core/theme/app_theme.dart';
import 'core/theme/theme_controller.dart';
import 'views/splash/splash_view.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // API_BASE_URL, MONEDA… salen de .env (ver README / .env.example)
  try {
    await dotenv.load(fileName: '.env');
  } catch (e) {
    debugPrint('No se pudo leer .env, se usan los valores de respaldo: $e');
  }
  await initializeDateFormatting('es');
  runApp(const MainApp());
}

class MainApp extends StatelessWidget {
  const MainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: temaApp,
      builder: (context, modo, _) => MaterialApp(
        title: '__APP_TITLE__',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        darkTheme: AppTheme.dark,
        themeMode: modo,
        home: const SplashView(),
      ),
    );
  }
}
