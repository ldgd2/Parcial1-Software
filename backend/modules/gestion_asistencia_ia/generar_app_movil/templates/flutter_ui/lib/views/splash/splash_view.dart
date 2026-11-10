import 'package:flutter/material.dart';

import '../../shared/widgets/animations.dart';
import '../home/home_shell.dart';

/// Pantalla de bienvenida animada.
class SplashView extends StatefulWidget {
  const SplashView({super.key});

  @override
  State<SplashView> createState() => _SplashViewState();
}

class _SplashViewState extends State<SplashView> with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 1300));

  @override
  void initState() {
    super.initState();
    _c.forward().whenComplete(() {
      if (mounted) Navigator.of(context).pushReplacement(appRoute(const HomeShell()));
    });
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final logo = CurvedAnimation(parent: _c, curve: const Interval(0, 0.6, curve: Curves.elasticOut));
    final texto = CurvedAnimation(parent: _c, curve: const Interval(0.35, 0.85, curve: Curves.easeOut));
    return Scaffold(
      body: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [scheme.primary, Color.lerp(scheme.primary, scheme.tertiary, 0.7)!],
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ScaleTransition(
              scale: logo,
              child: Container(
                width: 112,
                height: 112,
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(40),
                  borderRadius: BorderRadius.circular(32),
                ),
                child: const Icon(__HERO_ICON__, size: 56, color: Colors.white),
              ),
            ),
            const SizedBox(height: 28),
            FadeTransition(
              opacity: texto,
              child: SlideTransition(
                position: Tween(begin: const Offset(0, 0.4), end: Offset.zero).animate(texto),
                child: Column(
                  children: [
                    Text(
                      '__APP_TITLE__',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            color: Colors.white,
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '__APP_SUBTITLE__',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.white.withAlpha(210)),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
