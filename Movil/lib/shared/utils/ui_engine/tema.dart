import 'package:flutter/material.dart';

// ==========================================
// 1. PALETA DE COLORES (ALINEADA AL TEMA WEB)
// ==========================================
class AppColores {
  final Color primario;
  final Color secundario;
  final Color fondo;
  final Color fondoSecundario;
  final Color textoPrincipal;
  final Color textoSecundario;
  final Color error;
  final Color exito;
  final Color advertencia;
  final Color borde;

  const AppColores({
    required this.primario,
    required this.secundario,
    required this.fondo,
    required this.fondoSecundario,
    required this.textoPrincipal,
    required this.textoSecundario,
    required this.error,
    required this.exito,
    required this.advertencia,
    required this.borde,
  });

  // Tema Oscuro Oficial (Brand Web: #222831 / #393E46 / #DFD0B8 / #948979)
  static const oscuro = AppColores(
    primario: Color(0xFFDFD0B8), // Warm Sand / Gold Accent
    secundario: Color(0xFF948979), // Taupe / Bronze
    fondo: Color(0xFF222831), // Dark Charcoal Slate
    fondoSecundario: Color(0xFF393E46), // Surface Card / Container
    textoPrincipal: Color(0xFFFFFFFF), // Pure White
    textoSecundario: Color(0xFFDFD0B8), // Secondary Gold / Sand
    error: Color(0xFFEF4444),
    exito: Color(0xFF10B981),
    advertencia: Color(0xFFF59E0B),
    borde: Color(0xFF393E46),
  );

  // Tema Claro de Alto Contraste
  static const claro = AppColores(
    primario: Color(0xFF222831),
    secundario: Color(0xFF393E46),
    fondo: Color(0xFFF4F4F5),
    fondoSecundario: Colors.white,
    textoPrincipal: Color(0xFF18181B),
    textoSecundario: Color(0xFF71717A),
    error: Color(0xFFDC2626),
    exito: Color(0xFF059669),
    advertencia: Color(0xFFD97706),
    borde: Color(0xFFE4E4E7),
  );
}

// ==========================================
// 2. SISTEMA DE TIPOGRAFÍA
// ==========================================
class AppTextos {
  final TextStyle tituloLargo;
  final TextStyle titulo;
  final TextStyle subtitulo;
  final TextStyle cuerpo;
  final TextStyle cuerpoPequeno;
  final TextStyle boton;

  const AppTextos({
    required this.tituloLargo,
    required this.titulo,
    required this.subtitulo,
    required this.cuerpo,
    required this.cuerpoPequeno,
    required this.boton,
  });

  factory AppTextos.generar(AppColores colores) {
    return AppTextos(
      tituloLargo: TextStyle(
        fontSize: 28,
        fontWeight: FontWeight.bold,
        color: colores.textoPrincipal,
        letterSpacing: -0.5,
      ),
      titulo: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w700,
        color: colores.textoPrincipal,
        letterSpacing: -0.2,
      ),
      subtitulo: TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.w600,
        color: colores.textoSecundario,
      ),
      cuerpo: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.normal,
        color: colores.textoPrincipal,
      ),
      cuerpoPequeno: TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.normal,
        color: colores.textoSecundario,
      ),
      boton: const TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.w700,
        color: Color(0xFF222831),
      ),
    );
  }
}

// ==========================================
// 3. CONTROLADOR GLOBAL DEL TEMA
// ==========================================
class AppTheme {
  // Por defecto inicializamos con la paleta oscura de la web
  static AppColores colores = AppColores.oscuro;
  static AppTextos textos = AppTextos.generar(AppColores.oscuro);

  static void cambiarModo(bool esOscuro) {
    colores = esOscuro ? AppColores.oscuro : AppColores.claro;
    textos = AppTextos.generar(colores);
  }
}

// ==========================================
// 4. EXTENSIONES PARA BUILDCONTEXT
// ==========================================
extension ContextThemeExtension on BuildContext {
  AppColores get colores => AppTheme.colores;
  AppTextos get textos => AppTheme.textos;
}
