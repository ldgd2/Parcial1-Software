import 'package:flutter/material.dart';
import 'package:movil/core/storage/local_storage_service.dart';
import 'package:movil/shared/utils/ui_engine/tema.dart';
import 'package:movil/modules/visor/models/lienzo_model.dart';
import 'package:movil/modules/visor/controllers/visor_controller.dart';
import 'package:movil/modules/visor/views/widgets/nodo_clase_card.dart';
import 'package:movil/modules/visor/views/widgets/nodo_detalle_dialog.dart';
import 'package:movil/modules/visor/views/widgets/relaciones_painter.dart';
import 'package:movil/modules/visor/views/widgets/revisiones_sheet.dart';

class VisorArguments {
  final int proyectoId;
  final String proyectoNombre;
  final String codigoAcceso;
  final String? lienzoJsonInicial;
  final String rolUsuario;

  const VisorArguments({
    required this.proyectoId,
    required this.proyectoNombre,
    required this.codigoAcceso,
    this.lienzoJsonInicial,
    this.rolUsuario = 'viewer',
  });
}

class VisorScreen extends StatefulWidget {
  final VisorArguments arguments;

  const VisorScreen({super.key, required this.arguments});

  @override
  State<VisorScreen> createState() => _VisorScreenState();
}

class _VisorScreenState extends State<VisorScreen> {
  late final VisorController _controller;
  final TransformationController _transformationController = TransformationController();

  @override
  void initState() {
    super.initState();
    _controller = VisorController();
    _controller.addListener(_onStateChange);

    final usuario = LocalStorageService.usuario;
    final nickname = usuario != null ? (usuario['nombre'] ?? 'Viewer') : 'Viewer';

    // 1. Carga inicial vía REST
    _controller.cargarDatos(
      widget.arguments.proyectoId,
      lienzoInicial: widget.arguments.lienzoJsonInicial,
    );

    // 2. Conexión WebSocket en tiempo real
    if (widget.arguments.codigoAcceso.isNotEmpty) {
      _controller.iniciarWebSocket(
        codigoAcceso: widget.arguments.codigoAcceso,
        proyectoId: widget.arguments.proyectoId,
        nickname: nickname,
      );
    }
  }

  @override
  void dispose() {
    _controller.removeListener(_onStateChange);
    _controller.dispose();
    _transformationController.dispose();
    super.dispose();
  }

  void _onStateChange() {
    if (mounted) setState(() {});
  }

  void _abrirRevisionesSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return RevisionesSheet(
          notificaciones: _controller.notificaciones,
          tareas: _controller.tareas,
          roles: _controller.roles,
        );
      },
    );
  }

  void _abrirDetalleNodo(NodoModel nodo) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return NodoDetalleDialog(nodo: nodo);
      },
    );
  }

  void _centrarVista() {
    _transformationController.value = Matrix4.identity();
  }

  @override
  Widget build(BuildContext context) {
    final colores = AppColores.oscuro;
    final textos = AppTextos.generar(colores);
    final nodes = _controller.lienzoData.nodes;
    final relations = _controller.lienzoData.relations;

    double maxX = 1800;
    double maxY = 1400;
    for (final n in nodes) {
      if (n.x + n.width + 250 > maxX) maxX = n.x + n.width + 250;
      if (n.y + n.height + 250 > maxY) maxY = n.y + n.height + 250;
    }

    final Map<String, NodoModel> nodosMap = {for (final n in nodes) n.id: n};

    return Scaffold(
      backgroundColor: colores.fondo,
      appBar: AppBar(
        backgroundColor: colores.fondoSecundario,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.arguments.proyectoNombre,
              style: textos.titulo.copyWith(fontSize: 16),
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              widget.arguments.codigoAcceso,
              style: textos.cuerpoPequeno.copyWith(
                color: colores.secundario,
                fontSize: 11,
                fontFamily: 'monospace',
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.center_focus_strong_outlined),
            tooltip: 'Centrar',
            onPressed: _centrarVista,
          ),
          IconButton(
            icon: Icon(Icons.refresh, color: colores.primario),
            tooltip: 'Recargar',
            onPressed: _controller.isLoading
                ? null
                : () => _controller.cargarDatos(widget.arguments.proyectoId),
          ),
          IconButton(
            icon: const Icon(Icons.view_sidebar_outlined),
            tooltip: 'Feed y tareas',
            onPressed: _abrirRevisionesSheet,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            if (_controller.isLoading)
              const LinearProgressIndicator(minHeight: 2),

            Expanded(
              child: nodes.isEmpty && !_controller.isLoading
                  ? Center(
                      child: Container(
                        margin: const EdgeInsets.all(24),
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          color: colores.fondoSecundario,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: colores.borde),
                        ),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.dashboard_outlined, size: 40, color: colores.secundario),
                            const SizedBox(height: 10),
                            Text(
                              'El lienzo aún no tiene clases',
                              style: textos.subtitulo.copyWith(fontSize: 15),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Los elementos agregados desde la web aparecerán aquí automáticamente.',
                              textAlign: TextAlign.center,
                              style: textos.cuerpoPequeno,
                            ),
                          ],
                        ),
                      ),
                    )
                  : InteractiveViewer(
                      transformationController: _transformationController,
                      boundaryMargin: const EdgeInsets.all(400),
                      minScale: 0.15,
                      maxScale: 3.5,
                      constrained: false,
                      child: Container(
                        width: maxX,
                        height: maxY,
                        color: colores.fondo,
                        child: Stack(
                          clipBehavior: Clip.none,
                          children: [
                            // Relaciones vectoriales
                            CustomPaint(
                              size: Size(maxX, maxY),
                              painter: RelacionesPainter(
                                relaciones: relations,
                                nodosMap: nodosMap,
                                colorLinea: colores.secundario,
                                colorTexto: colores.primario,
                              ),
                            ),

                            // Nodos de clase
                            ...nodes.map((nodo) {
                              return NodoClaseCard(
                                nodo: nodo,
                                onTap: () => _abrirDetalleNodo(nodo),
                              );
                            }),
                          ],
                        ),
                      ),
                    ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.small(
        backgroundColor: colores.fondoSecundario,
        foregroundColor: colores.primario,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: colores.borde),
        ),
        tooltip: 'Feed de actividad y tareas',
        onPressed: _abrirRevisionesSheet,
        child: const Icon(Icons.feed_outlined, size: 20),
      ),
    );
  }
}
