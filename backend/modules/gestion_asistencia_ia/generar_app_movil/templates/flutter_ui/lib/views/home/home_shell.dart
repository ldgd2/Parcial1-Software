import 'package:flutter/material.dart';

import 'dashboard_view.dart';
import 'modules_view.dart';
import 'settings_view.dart';

/// Estructura principal: Inicio · Módulos · Ajustes.
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _indice = 0;

  static const _paginas = <Widget>[DashboardView(), ModulesView(), SettingsView()];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 280),
        switchInCurve: Curves.easeOutCubic,
        transitionBuilder: (child, anim) => FadeTransition(
          opacity: anim,
          child: ScaleTransition(scale: Tween(begin: 0.98, end: 1.0).animate(anim), child: child),
        ),
        child: KeyedSubtree(key: ValueKey(_indice), child: _paginas[_indice]),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _indice,
        onDestinationSelected: (i) => setState(() => _indice = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home_rounded), label: 'Inicio'),
          NavigationDestination(icon: Icon(Icons.grid_view_outlined), selectedIcon: Icon(Icons.grid_view_rounded), label: 'Módulos'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings_rounded), label: 'Ajustes'),
        ],
      ),
    );
  }
}
