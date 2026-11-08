class ProyectoModel {
  final int id;
  final String nombre;
  final String descripcion;
  final String codigoAcceso;
  final int anfitrionId;
  final String rolUsuario;
  final String? githubRepoUrl;

  const ProyectoModel({
    required this.id,
    required this.nombre,
    required this.descripcion,
    required this.codigoAcceso,
    required this.anfitrionId,
    required this.rolUsuario,
    this.githubRepoUrl,
  });

  factory ProyectoModel.fromJson(Map<String, dynamic> json) {
    return ProyectoModel(
      id: json['id'] ?? json['proyecto_id'] ?? 0,
      nombre: json['nombre'] ?? json['proyecto_nombre'] ?? 'Sin nombre',
      descripcion: json['descripcion'] ?? '',
      codigoAcceso: json['codigo_acceso'] ?? '',
      anfitrionId: json['anfitrion_id'] ?? 0,
      rolUsuario: json['rol_usuario'] ?? json['rol_proyecto'] ?? 'espectador',
      githubRepoUrl: json['github_repo_url'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nombre': nombre,
      'descripcion': descripcion,
      'codigo_acceso': codigoAcceso,
      'anfitrion_id': anfitrionId,
      'rol_usuario': rolUsuario,
      'github_repo_url': githubRepoUrl,
    };
  }
}

class UnirseSalaModel {
  final String acceso;
  final String? mensaje;
  final int proyectoId;
  final String proyectoNombre;
  final String? codigoAcceso;
  final String? lienzoJson;
  final String? githubRepoUrl;

  const UnirseSalaModel({
    required this.acceso,
    this.mensaje,
    required this.proyectoId,
    required this.proyectoNombre,
    this.codigoAcceso,
    this.lienzoJson,
    this.githubRepoUrl,
  });

  factory UnirseSalaModel.fromJson(Map<String, dynamic> json) {
    return UnirseSalaModel(
      acceso: json['acceso'] ?? 'aprobado',
      mensaje: json['mensaje'],
      proyectoId: json['proyecto_id'] ?? 0,
      proyectoNombre: json['proyecto_nombre'] ?? 'Sala UML',
      codigoAcceso: json['codigo_acceso'],
      lienzoJson: json['lienzo_json'],
      githubRepoUrl: json['github_repo_url'],
    );
  }
}

