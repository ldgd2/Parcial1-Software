import 'package:flutter/material.dart';

/// Parámetro de una acción (método del diagrama).
class ParamInfo {
  final String nombre;
  final String etiqueta;

  /// texto | entero | decimal | booleano | fecha | fechahora
  final String tipo;

  const ParamInfo(this.nombre, this.etiqueta, this.tipo);
}

/// Método de negocio del diagrama, expuesto por el backend como POST /api/<entidad>/<método>.
class AccionInfo {
  final String nombre;
  final String etiqueta;
  final String retorno;
  final List<ParamInfo> parametros;
  final Future<dynamic> Function(Map<String, dynamic> parametros) ejecutar;

  const AccionInfo({
    required this.nombre,
    required this.etiqueta,
    required this.retorno,
    required this.parametros,
    required this.ejecutar,
  });
}

/// Dato listo para mostrar (etiqueta, valor e ícono).
class CampoVista {
  final String etiqueta;
  final String valor;
  final IconData icono;

  const CampoVista(this.etiqueta, this.valor, this.icono);
}

class ResumenItem {
  final String titulo;
  final String subtitulo;
  const ResumenItem(this.titulo, this.subtitulo);
}

/// Un módulo de la app (una clase del diagrama).
class ModuloInfo {
  final String nombre;
  final String plural;
  final String descripcion;
  final IconData icono;
  final Color color;
  final Future<int> Function() contar;
  final Future<List<ResumenItem>> Function() recientes;
  final Widget Function() lista;
  final Widget Function() nuevo;
  final List<AccionInfo> acciones;

  const ModuloInfo({
    required this.nombre,
    required this.plural,
    required this.descripcion,
    required this.icono,
    required this.color,
    required this.contar,
    required this.recientes,
    required this.lista,
    required this.nuevo,
    required this.acciones,
  });
}
