class VisorEndpoints {
  static String lienzo(int proyectoId) => '/salas/$proyectoId/lienzo';
  static String tareas(int proyectoId) => '/api/ia/tareas/proyecto/$proyectoId/todas';
  static String roles(int proyectoId) => '/api/ia/roles/proyecto/$proyectoId';
}

