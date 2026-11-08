import 'package:flutter/material.dart';
import 'views/screens/login_screen.dart';

class AuthRoutes {
  static const String login = '/login';

  static Map<String, WidgetBuilder> get routes => {
        login: (context) => const LoginScreen(),
      };
}

