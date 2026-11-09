import 'package:flutter/material.dart';
import 'package:movil/shared/utils/ui_engine/tema.dart';
import 'package:movil/modules/visor/models/lienzo_model.dart';

class RevisionesSheet extends StatefulWidget {
  final List<RevisionNotificacionModel> notificaciones;
  final List<TareaVisorModel> tareas;
  final List<RolVisorModel> roles;

  const RevisionesSheet({
    super.key,
    required this.notificaciones,
    required this.tareas,
    required this.roles,
  });

  @override
  State<RevisionesSheet> createState() => _RevisionesSheetState();
}

class _RevisionesSheetState extends State<RevisionesSheet> with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Color _colorEstadoTarea(String estado) {
    switch (estado.toLowerCase()) {
      case 'completada':
      case 'done':
        return const Color(0xFF10B981); // Emerald
      case 'en_progreso':
      case 'in_progress':
        return const Color(0xFFF59E0B); // Amber
      default:
        return const Color(0xFF948979); // Muted bronze
    }
  }

  @override
  Widget build(BuildContext context) {
    final colores = AppColores.oscuro;
    final textos = AppTextos.generar(colores);

    return Container(
      height: MediaQuery.of(context).size.height * 0.8,
      decoration: BoxDecoration(
        color: colores.fondoSecundario,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
        border: Border.all(color: colores.borde),
      ),
      child: Column(
        children: [
          // Drag handle
          Container(
            width: 38,
            height: 4,
            margin: const EdgeInsets.only(top: 12, bottom: 8),
            decoration: BoxDecoration(
              color: colores.secundario.withOpacity(0.4),
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Row(
              children: [
                Icon(Icons.feed_outlined, color: colores.primario, size: 22),
                const SizedBox(width: 8),
                Text('Actividad y Tareas', style: textos.titulo.copyWith(fontSize: 16)),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),

          TabBar(
            controller: _tabController,
            labelColor: colores.primario,
            unselectedLabelColor: colores.secundario,
            indicatorColor: colores.primario,
            tabs: [
              Tab(text: 'Actividad (${widget.notificaciones.length})'),
              Tab(text: 'Tareas (${widget.tareas.length})'),
              Tab(text: 'Roles (${widget.roles.length})'),
            ],
          ),

          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                // 1. Tab Actividad
                widget.notificaciones.isEmpty
                    ? Center(
                        child: Text(
                          'Sin actividad reciente',
                          style: textos.cuerpoPequeno,
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: widget.notificaciones.length,
                        itemBuilder: (context, index) {
                          final notif = widget.notificaciones[index];
                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: colores.fondo,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: colores.borde),
                            ),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  notif.tipo == 'rol'
                                      ? Icons.badge_outlined
                                      : Icons.assignment_outlined,
                                  color: colores.primario,
                                  size: 20,
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Expanded(
                                            child: Text(
                                              notif.titulo,
                                              style: const TextStyle(
                                                color: Colors.white,
                                                fontWeight: FontWeight.bold,
                                                fontSize: 13,
                                              ),
                                            ),
                                          ),
                                          Text(
                                            '${notif.fecha.hour.toString().padLeft(2, '0')}:${notif.fecha.minute.toString().padLeft(2, '0')}',
                                            style: TextStyle(
                                              color: colores.secundario,
                                              fontSize: 11,
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        notif.detalle,
                                        style: textos.cuerpoPequeno,
                                      ),
                                      if (notif.autor != null && notif.autor!.isNotEmpty) ...[
                                        const SizedBox(height: 4),
                                        Text(
                                          'Asignado a: ${notif.autor}',
                                          style: TextStyle(
                                            color: colores.secundario,
                                            fontSize: 10.5,
                                          ),
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),

                // 2. Tab Tareas del Equipo
                widget.tareas.isEmpty
                    ? Center(
                        child: Text(
                          'No hay tareas registradas para este proyecto.',
                          style: textos.cuerpoPequeno,
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: widget.tareas.length,
                        itemBuilder: (context, index) {
                          final tarea = widget.tareas[index];
                          final badgeColor = _colorEstadoTarea(tarea.estado);
                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: colores.fondo,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: colores.borde),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Expanded(
                                      child: Text(
                                        tarea.titulo,
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontWeight: FontWeight.bold,
                                          fontSize: 13,
                                        ),
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: badgeColor.withOpacity(0.2),
                                        borderRadius: BorderRadius.circular(4),
                                        border: Border.all(color: badgeColor),
                                      ),
                                      child: Text(
                                        tarea.estado.toUpperCase(),
                                        style: TextStyle(
                                          color: badgeColor,
                                          fontSize: 9.5,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Text(tarea.descripcion, style: textos.cuerpoPequeno),
                                const SizedBox(height: 8),
                                Row(
                                  children: [
                                    Icon(Icons.work_outline, size: 12, color: colores.secundario),
                                    const SizedBox(width: 4),
                                    Text(
                                      tarea.rolRequerido,
                                      style: TextStyle(color: colores.secundario, fontSize: 11),
                                    ),
                                    if (tarea.colaboradorNombre != null) ...[
                                      const SizedBox(width: 12),
                                      Icon(Icons.person_outline, size: 12, color: colores.primario),
                                      const SizedBox(width: 4),
                                      Text(
                                        tarea.colaboradorNombre!,
                                        style: TextStyle(color: colores.primario, fontSize: 11),
                                      ),
                                    ],
                                  ],
                                ),
                              ],
                            ),
                          );
                        },
                      ),

                // 3. Tab Roles Asignados
                widget.roles.isEmpty
                    ? Center(
                        child: Text(
                          'No hay roles registrados en este proyecto.',
                          style: textos.cuerpoPequeno,
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: widget.roles.length,
                        itemBuilder: (context, index) {
                          final rol = widget.roles[index];
                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: colores.fondo,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: colores.borde),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      rol.usuarioNombre,
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 14,
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: colores.primario.withOpacity(0.15),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(
                                        rol.rolAsignado,
                                        style: TextStyle(
                                          color: colores.primario,
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                if (rol.habilidades.isNotEmpty) ...[
                                  const SizedBox(height: 8),
                                  Wrap(
                                    spacing: 4,
                                    runSpacing: 4,
                                    children: rol.habilidades.map((hab) {
                                      return Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                                        decoration: BoxDecoration(
                                          color: colores.fondoSecundario,
                                          borderRadius: BorderRadius.circular(3),
                                        ),
                                        child: Text(
                                          hab,
                                          style: TextStyle(
                                            color: colores.secundario,
                                            fontSize: 9.5,
                                          ),
                                        ),
                                      );
                                    }).toList(),
                                  ),
                                ],
                              ],
                            ),
                          );
                        },
                      ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

