class ProyectosEndpoints {
  static const String misProyectos = '/proyectos/mis-proyectos';
  static String unirseSala(String codigo) => '/salas/unirse/$codigo';
  static String lienzo(int proyectoId) => '/salas/$proyectoId/lienzo';
}

