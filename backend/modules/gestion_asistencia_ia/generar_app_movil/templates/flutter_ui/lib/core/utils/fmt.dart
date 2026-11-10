import 'dart:convert';

import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:intl/intl.dart';

/// Formatos de presentación (dinero, fechas, números) en español.
class Fmt {
  /// Símbolo de moneda: MONEDA en el archivo .env (por defecto "$")
  static String get moneda {
    if (!dotenv.isInitialized) return r'$';
    final m = dotenv.maybeGet('MONEDA')?.trim();
    return (m == null || m.isEmpty) ? r'$' : m;
  }

  static String dinero(num? v) =>
      v == null ? '—' : '$moneda ${NumberFormat('#,##0.00', 'es').format(v)}';

  static String numero(num? v) => v == null ? '—' : NumberFormat.decimalPattern('es').format(v);

  static String fecha(DateTime? d) => d == null ? 'Sin fecha' : DateFormat('d MMM y', 'es').format(d);

  static String si(bool? v) => v == true ? 'Sí' : 'No';

  static String texto(String? s) => (s == null || s.trim().isEmpty) ? '—' : s.trim();

  static String iniciales(String s) {
    final partes = s.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    if (partes.isEmpty) return '?';
    if (partes.length == 1) return partes.first.substring(0, 1).toUpperCase();
    return (partes[0].substring(0, 1) + partes[1].substring(0, 1)).toUpperCase();
  }

  static String saludo() {
    final h = DateTime.now().hour;
    if (h < 12) return 'Buenos días';
    if (h < 19) return 'Buenas tardes';
    return 'Buenas noches';
  }

  /// Resultado de una acción del backend, legible
  static String resultado(dynamic v) {
    if (v == null) return 'Acción realizada correctamente.';
    if (v is num) return numero(v);
    if (v is bool) return si(v);
    if (v is String) return v.isEmpty ? 'Acción realizada correctamente.' : v;
    return const JsonEncoder.withIndent('  ').convert(v);
  }
}
