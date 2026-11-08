import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_input_password.dart';

/// Validador y Analizador de Seguridad de Contraseñas (`CustomPasswordCreateInput`):
/// Evalúa entropía real, diversidad de caracteres, longitud y passphrases.
/// Penaliza palabras comunes o secuencias únicamente si son dominantes en contraseñas cortas,
/// permitiendo passphrases y frases largas combinadas con símbolos y números sin falsos positivos.
class CustomPasswordCreateInput extends StatefulWidget {
  final String label;
  final String hint;
  final ValueChanged<String>? onChanged;
  final Function(bool isValid, int points, String level)? onValidationChanged;
  final TextEditingController? controller;
  final Color? fillColor;
  final bool showChecklist;
  final bool showStrengthBar;
  final bool showPoints;

  const CustomPasswordCreateInput({
    super.key,
    this.label = "Crear Nueva Contraseña",
    this.hint = "Ingresa una contraseña segura",
    this.onChanged,
    this.onValidationChanged,
    this.controller,
    this.fillColor,
    this.showChecklist = true,
    this.showStrengthBar = true,
    this.showPoints = true,
  });

  @override
  State<CustomPasswordCreateInput> createState() => _CustomPasswordCreateInputState();
}

class _CustomPasswordCreateInputState extends State<CustomPasswordCreateInput> {
  String _currentPassword = "";

  // 1. Reglas fundamentales de seguridad
  bool get _hasMinLength => _currentPassword.length >= 8;
  bool get _hasUppercase => RegExp(r'[A-Z]').hasMatch(_currentPassword);
  bool get _hasLowercase => RegExp(r'[a-z]').hasMatch(_currentPassword);
  bool get _hasNumber => RegExp(r'[0-9]').hasMatch(_currentPassword);
  bool get _hasSpecialChar =>
      RegExp(r'[!@#\$%^&*(),.?":{}|<>_\-+=\[\]\\\/]').hasMatch(_currentPassword);

  bool get isAllValid =>
      _hasMinLength && _hasUppercase && _hasLowercase && _hasNumber && _hasSpecialChar;

  bool get _isDominantDictionaryWord {
    if (_currentPassword.isEmpty) return false;
    // En passphrases largas (>= 18 caracteres) con símbolos y números, las palabras embebidas son seguras.
    if (_currentPassword.length >= 18 && isAllValid) return false;

    String normalized = _currentPassword.toLowerCase()
        .replaceAll('@', 'a')
        .replaceAll('0', 'o')
        .replaceAll('1', 'i')
        .replaceAll('3', 'e')
        .replaceAll('\$', 's');

    final commonWords = [
      "password", "admin", "contrasena", "clave", "welcome", "usuario",
      "root", "master", "dragon", "futbol", "familia", "acceso", "login"
    ];

    for (final word in commonWords) {
      if (normalized.contains(word)) {
        // Es dominante si la contraseña es corta (<14) o si la palabra ocupa más del 50% de la clave
        if (_currentPassword.length < 14 || (word.length / _currentPassword.length) > 0.45) {
          return true;
        }
      }
    }
    return false;
  }

  /// Detección de secuencias dominantes (solo penaliza si la clave es corta o no tiene variedad)
  bool get _isDominantSequence {
    if (_currentPassword.length >= 18 && isAllValid) return false;

    final lower = _currentPassword.toLowerCase();
    final walks = [
      "123456", "654321", "12345", "54321", "abcdef", "qwerty", "asdfgh", "zxcvbn"
    ];

    for (final walk in walks) {
      if (lower.contains(walk)) {
        if (_currentPassword.length < 14 || (walk.length / _currentPassword.length) > 0.45) {
          return true;
        }
      }
    }
    return false;
  }

  /// Detección de patrones cíclicos puros (ej. 'a1a1a1', '121212', 'abab') en claves cortas/medianas
  bool get _hasCyclicPatterns {
    if (_currentPassword.length < 6) return false;
    if (_currentPassword.length >= 20 && isAllValid) return false;
    return RegExp(r'(.{2,4})\1{2,}').hasMatch(_currentPassword);
  }

  /// Detección de caracteres idénticos continuos (ej. 'aaaa', '1111')
  bool get _hasRepeatedChars {
    if (_currentPassword.length < 10) {
      return RegExp(r'(.)\1{2,}').hasMatch(_currentPassword);
    }
    return RegExp(r'(.)\1{3,}').hasMatch(_currentPassword);
  }

  /// Ratio de diversidad / caracteres únicos (0.0 a 1.0)
  double get _uniqueCharRatio {
    if (_currentPassword.isEmpty) return 0.0;
    final uniqueCount = _currentPassword.split('').toSet().length;
    return uniqueCount / _currentPassword.length;
  }

  // 3. Motor de Puntuación Proporcional
  int get _calculatedPoints {
    if (_currentPassword.isEmpty) return 0;

    int points = 0;
    final length = _currentPassword.length;

    // --- A) PUNTOS POSITIVOS (Longitud masiva y Entropía) ---
    if (length >= 24) {
      points += 55; // Passphrase extremadamente robusta
    } else if (length >= 18) {
      points += 45;
    } else if (length >= 14) {
      points += 35;
    } else if (length >= 10) {
      points += 25;
    } else if (length >= 8) {
      points += 15;
    } else {
      points += 5;
    }

    // Puntos por variedad de conjuntos
    if (_hasLowercase) points += 10;
    if (_hasUppercase) points += 10;
    if (_hasNumber) points += 10;
    if (_hasSpecialChar) points += 15;

    // Bonus por alta longitud y cumplimiento total
    if (length >= 14 && isAllValid) points += 10;
    if (length >= 22 && isAllValid) points += 10;

    // --- B) DEDUCCIONES CONTEXTUALES ---
    int penalties = 0;

    // 1. Penalización si una palabra de diccionario domina la clave corta
    if (_isDominantDictionaryWord) {
      penalties += 30;
    }

    // 2. Penalización si una secuencia predecible domina la clave
    if (_isDominantSequence) {
      penalties += 20;
    }

    // 3. Penalización por patrones cíclicos (ej. 'a1a1a1')
    if (_hasCyclicPatterns) {
      penalties += 20;
    }

    // 4. Penalización por repetición de un mismo carácter ('aaaa')
    if (_hasRepeatedChars) {
      penalties += 15;
    }

    // 5. Penalización por muy bajo ratio de unicidad en claves cortas/medianas
    if (length >= 8 && length < 20 && _uniqueCharRatio < 0.45) {
      penalties += 15;
    }

    // Aplicar penalizaciones
    points = (points - penalties);

    // --- C) BARRERAS ESTRICTAS DE REGLAS BASE ---
    // Si no cumple las 5 reglas obligatorias, tope estricto a 30 pts
    if (!isAllValid) {
      points = points.clamp(0, 30);
    }

    // Si tiene menos de 8 caracteres, tope estricto a 15 pts
    if (length < 8) {
      points = points.clamp(0, 15);
    }

    return points.clamp(0, 100);
  }

  // 4. Clasificación
  String get _securityLevel {
    final pts = _calculatedPoints;
    if (_currentPassword.isEmpty) return "Sin datos";
    if (pts < 30) return "No es segura";
    if (pts < 50) return "Poco segura";
    if (pts < 70) return "Medio segura";
    if (pts < 90) return "Segura";
    return "Muy segura";
  }

  Color _getStrengthColor(BuildContext context, int points) {
    if (points < 30) return context.colores.error;
    if (points < 50) return Colors.orange;
    if (points < 70) return context.colores.advertencia;
    if (points < 90) return const Color(0xFF10B981); 
    return context.colores.exito;
  }


  String? get _securityWarning {
    if (_currentPassword.isEmpty) return null;

    if (_calculatedPoints < 70) {
      if (_isDominantDictionaryWord) {
        return "Evita usar contraseñas basadas principalmente en palabras comunes (ej. 'password', 'admin').";
      }
      if (_isDominantSequence) {
        return "Evita secuencias obvias de teclado o números (ej. '123456', 'qwerty').";
      }
      if (_hasCyclicPatterns) {
        return "Evita patrones repetitivos como secuencias cíclicas (ej. 'a1a1a1').";
      }
      if (_hasRepeatedChars) {
        return "Evita repetir el mismo carácter varias veces seguidas.";
      }
    }
    return null;
  }

  void _onPasswordChanged(String value) {
    setState(() => _currentPassword = value);
    widget.onChanged?.call(value);
    widget.onValidationChanged?.call(isAllValid, _calculatedPoints, _securityLevel);
  }

  Widget _buildCheckItem(BuildContext context, String text, bool isMet) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.5),
      child: Row(
        children: [
          Icon(
            isMet ? Icons.check_circle_rounded : Icons.radio_button_unchecked,
            size: 16,
            color: isMet ? themeColores.exito : themeColores.textoSecundario.withValues(alpha: 0.5),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: themeTextos.cuerpoPequeno.copyWith(
                fontSize: 12,
                fontWeight: isMet ? FontWeight.w600 : FontWeight.normal,
                color: isMet ? themeColores.textoPrincipal : themeColores.textoSecundario.withValues(alpha: 0.8),
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final points = _calculatedPoints;
    final progress = points / 100.0;
    final strengthColor = _getStrengthColor(context, points);
    final warning = _securityWarning;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // Campo de entrada de contraseña
        CustomPasswordInput(
          label: widget.label,
          hint: widget.hint,
          fillColor: widget.fillColor,
          controller: widget.controller,
          isRequired: true,
          onChanged: _onPasswordChanged,
        ),

        // Barra de Fortaleza con Puntaje Numérico
        if (widget.showStrengthBar && _currentPassword.isNotEmpty) ...[
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: progress,
                    backgroundColor: themeColores.borde.withValues(alpha: 0.4),
                    valueColor: AlwaysStoppedAnimation<Color>(strengthColor),
                    minHeight: 6,
                  ),
                ),
              ),
              const SizedBox(width: 10),
              if (widget.showPoints) ...[
                Text(
                  "$points/100 pts",
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: themeColores.textoSecundario,
                  ),
                ),
                const SizedBox(width: 6),
              ],
              Text(
                _securityLevel,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: strengthColor,
                ),
              ),
            ],
          ),
        ],

        // Aviso de seguridad contextual con Icono nativo
        if (warning != null) ...[
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                points < 50 ? Icons.warning_amber_rounded : Icons.info_outline_rounded,
                size: 14,
                color: points < 50 ? themeColores.error : Colors.orange[800],
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  warning,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                    color: points < 50 ? themeColores.error : Colors.orange[800],
                  ),
                ),
              ),
            ],
          ),
        ],

        // Lista interactiva de requisitos de seguridad (Checklist)
        if (widget.showChecklist) ...[
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: themeColores.fondoSecundario.withValues(alpha: 0.6),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: isAllValid
                    ? themeColores.exito.withValues(alpha: 0.4)
                    : themeColores.borde.withValues(alpha: 0.4),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildCheckItem(context, "Mínimo 8 caracteres", _hasMinLength),
                _buildCheckItem(context, "Al menos una letra mayúscula (A-Z)", _hasUppercase),
                _buildCheckItem(context, "Al menos una letra minúscula (a-z)", _hasLowercase),
                _buildCheckItem(context, "Al menos un número (0-9)", _hasNumber),
                _buildCheckItem(context, "Al menos un carácter especial (!@#\$%...)", _hasSpecialChar),
              ],
            ),
          ),
        ],
      ],
    );
  }
}
