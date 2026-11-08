import 'package:flutter/material.dart';
import 'package:movil/core/storage/local_storage_service.dart';
import 'package:movil/shared/utils/ui_engine/tema.dart';
import 'package:movil/shared/widgets/inputs/custom_input.dart';
import 'package:movil/modules/auth/auth_routes.dart';
import 'package:movil/modules/visor/visor_routes.dart';
import 'package:movil/modules/visor/views/screens/visor_screen.dart';
import 'package:movil/modules/proyectos/controllers/proyectos_controller.dart';
import 'package:movil/modules/proyectos/models/proyecto_model.dart';

class ProyectosScreen extends StatefulWidget {
  const ProyectosScreen({super.key});

  @override
  State<ProyectosScreen> createState() => _ProyectosScreenState();
}

class _ProyectosScreenState extends State<ProyectosScreen> {
  late final ProyectosController _controller;
  final _codigoController = TextEditingController();
  final _busquedaController = TextEditingController();
  String _filtroBusqueda = '';

  @override
  void initState() {
    super.initState();
    _controller = ProyectosController();
    _controller.addListener(_onStateChange);
    _controller.cargarProyectos();
    _busquedaController.addListener(() {
      setState(() {
        _filtroBusqueda = _busquedaController.text.trim().toLowerCase();
      });
    });
  }

  @override
  void dispose() {
    _controller.removeListener(_onStateChange);
    _codigoController.dispose();
    _busquedaController.dispose();
    super.dispose();
  }

  void _onStateChange() {
    if (mounted) setState(() {});
  }

  Future<void> _unirsePorCodigo(String codigo) async {
    final clean = codigo.trim();
    if (clean.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa un código de sala')),
      );
      return;
    }

    final res = await _controller.unirsePorCodigo(clean);
    if (res != null && mounted) {
      Navigator.pushNamed(
        context,
        VisorRoutes.visor,
        arguments: VisorArguments(
          proyectoId: res.proyectoId,
          proyectoNombre: res.proyectoNombre,
          codigoAcceso: res.codigoAcceso ?? clean,
          lienzoJsonInicial: res.lienzoJson,
          rolUsuario: 'viewer',
        ),
      );
    }
  }

  void _abrirVisorDesdeProyecto(ProyectoModel proyecto) {
    Navigator.pushNamed(
      context,
      VisorRoutes.visor,
      arguments: VisorArguments(
        proyectoId: proyecto.id,
        proyectoNombre: proyecto.nombre,
        codigoAcceso: proyecto.codigoAcceso,
        rolUsuario: proyecto.rolUsuario,
      ),
    );
  }

  void _cerrarSesion() {
    LocalStorageService.cerrarSesion();
    Navigator.pushReplacementNamed(context, AuthRoutes.login);
  }

  @override
  Widget build(BuildContext context) {
    final colores = AppColores.oscuro;
    final textos = AppTextos.generar(colores);

    final proyectosFiltrados = _controller.proyectos.where((p) {
      if (_filtroBusqueda.isEmpty) return true;
      return p.nombre.toLowerCase().contains(_filtroBusqueda) ||
          p.codigoAcceso.toLowerCase().contains(_filtroBusqueda) ||
          p.descripcion.toLowerCase().contains(_filtroBusqueda);
    }).toList();

    return Scaffold(
      backgroundColor: colores.fondo,
      appBar: AppBar(
        backgroundColor: colores.fondoSecundario,
        elevation: 0,
        title: Text('Proyectos', style: textos.titulo),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: colores.primario),
            tooltip: 'Actualizar',
            onPressed: _controller.isLoading ? null : _controller.cargarProyectos,
          ),
          IconButton(
            icon: Icon(Icons.logout, color: colores.secundario),
            tooltip: 'Salir',
            onPressed: _cerrarSesion,
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: colores.primario,
          backgroundColor: colores.fondoSecundario,
          onRefresh: _controller.cargarProyectos,
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            children: [
              // Barra para unirse por código directo
              Row(
                children: [
                  Expanded(
                    child: CustomInput(
                      hint: 'Código de acceso a la sala...',
                      controller: _codigoController,
                      prefixIcon: Icons.qr_code_outlined,
                      onSubmitted: _unirsePorCodigo,
                    ),
                  ),
                  const SizedBox(width: 8),
                  SizedBox(
                    height: 48,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: colores.primario,
                        foregroundColor: colores.fondo,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                      ),
                      onPressed: _controller.isLoading
                          ? null
                          : () => _unirsePorCodigo(_codigoController.text),
                      child: const Text('Unirse', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),

              if (LocalStorageService.codigosRecientes.isNotEmpty) ...[
                const SizedBox(height: 10),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: LocalStorageService.codigosRecientes.map((code) {
                    return ActionChip(
                      backgroundColor: colores.fondoSecundario,
                      side: BorderSide(color: colores.borde),
                      label: Text(
                        code.length > 10 ? '${code.substring(0, 8)}...' : code,
                        style: textos.cuerpoPequeno.copyWith(color: colores.primario, fontSize: 11),
                      ),
                      onPressed: () {
                        _codigoController.text = code;
                        _unirsePorCodigo(code);
                      },
                    );
                  }).toList(),
                ),
              ],

              const SizedBox(height: 16),

              // Buscador de proyectos locales
              if (_controller.proyectos.length > 3) ...[
                CustomInput(
                  hint: 'Buscar proyecto...',
                  controller: _busquedaController,
                  prefixIcon: Icons.search,
                ),
                const SizedBox(height: 14),
              ],

              if (_controller.errorMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: colores.error.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: colores.error.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    _controller.errorMessage!,
                    style: textos.cuerpoPequeno.copyWith(color: colores.error),
                  ),
                ),
                const SizedBox(height: 12),
              ],

              if (_controller.isLoading && _controller.proyectos.isEmpty) ...[
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32),
                    child: CircularProgressIndicator(),
                  ),
                ),
              ] else if (proyectosFiltrados.isEmpty) ...[
                Container(
                  margin: const EdgeInsets.only(top: 24),
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: colores.fondoSecundario,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: colores.borde),
                  ),
                  child: Column(
                    children: [
                      Icon(Icons.folder_open_outlined, size: 36, color: colores.secundario),
                      const SizedBox(height: 10),
                      Text(
                        'Sin proyectos disponibles',
                        style: textos.subtitulo.copyWith(fontSize: 14),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Ingresa un código de acceso arriba para unirte a una sala existente.',
                        textAlign: TextAlign.center,
                        style: textos.cuerpoPequeno,
                      ),
                    ],
                  ),
                ),
              ] else ...[
                ...proyectosFiltrados.map((proyecto) {
                  return InkWell(
                    borderRadius: BorderRadius.circular(10),
                    onTap: () => _abrirVisorDesdeProyecto(proyecto),
                    child: Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: colores.fondoSecundario,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: colores.borde),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: colores.fondo,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Icon(Icons.account_tree_outlined, color: colores.primario, size: 20),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  proyecto.nombre,
                                  style: textos.subtitulo.copyWith(fontSize: 15),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                if (proyecto.descripcion.isNotEmpty) ...[
                                  const SizedBox(height: 2),
                                  Text(
                                    proyecto.descripcion,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: textos.cuerpoPequeno.copyWith(fontSize: 12),
                                  ),
                                ],
                                const SizedBox(height: 4),
                                Text(
                                  proyecto.codigoAcceso,
                                  style: textos.cuerpoPequeno.copyWith(
                                    color: colores.secundario,
                                    fontSize: 11,
                                    fontFamily: 'monospace',
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Icon(Icons.chevron_right, color: colores.secundario, size: 20),
                        ],
                      ),
                    ),
                  );
                }),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
