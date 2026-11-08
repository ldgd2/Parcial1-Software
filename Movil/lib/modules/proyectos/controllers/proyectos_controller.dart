import 'package:flutter/material.dart';
import 'package:movil/core/storage/local_storage_service.dart';
import 'package:movil/modules/proyectos/models/proyecto_model.dart';
import 'package:movil/modules/proyectos/services/proyectos_service.dart';

class ProyectosController extends ChangeNotifier {
  final ProyectosService _service;

  ProyectosController({ProyectosService? service})
      : _service = service ?? ProyectosService();

  bool _isLoading = false;
  String? _errorMessage;
  List<ProyectoModel> _proyectos = [];

  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  List<ProyectoModel> get proyectos => _proyectos;

  Future<void> cargarProyectos() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _proyectos = await _service.listarMisProyectos();
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _isLoading = false;
      _errorMessage = e.toString().replaceAll('Exception: ', '');
      notifyListeners();
    }
  }

  Future<UnirseSalaModel?> unirsePorCodigo(String codigo) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _service.unirsePorCodigo(codigo);
      LocalStorageService.agregarCodigoReciente(codigo);
      _isLoading = false;
      notifyListeners();
      return res;
    } catch (e) {
      _isLoading = false;
      _errorMessage = e.toString().replaceAll('Exception: ', '');
      notifyListeners();
      return null;
    }
  }
}

