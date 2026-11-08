import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_loader_dots.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Indicador "Escribiendo..." (Typing indicator).
/// Ideal para chats, mensajes o procesamiento de IA.
class CustomLoaderTyping extends StatelessWidget {
  final bool isDark;
  
  const CustomLoaderTyping({
    super.key,
    this.isDark = false,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    
    final bgColor = isDark ? themeColores.fondoSecundario : themeColores.borde;
    final dotsColor = isDark ? Colors.white : themeColores.textoSecundario;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(20),
          topRight: Radius.circular(20),
          bottomRight: Radius.circular(20),
          bottomLeft: Radius.circular(4), // Pico de chat
        ),
      ),
      child: CustomLoaderDots(
        size: 6,
        color: dotsColor,
        duration: 400.ms,
      ),
    );
  }
}
