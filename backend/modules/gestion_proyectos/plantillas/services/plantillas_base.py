"""
Plantillas base (CU42). Se definen en compacto y se expanden al formato del lienzo
({nodes, relations} como DiagramState del frontend). Al aplicarlas, el frontend
genera ids nuevos (los ids de elementos son únicos en toda la base).
"""
from typing import Any, Dict, List

COLOR = "#ed8936"

# nombre: (atributos "vis nombre:tipo", métodos "nombre(params):retorno")
_BASE: Dict[str, Dict[str, Any]] = {
    "ventas": {
        "nombre": "Ventas / Comercio",
        "descripcion": "Clientes, productos, pedidos con detalle y pagos.",
        "clases": {
            "Cliente": (["PK id:int", "+ nombre:String", "+ email:String", "+ telefono:String"], ["registrar():void"]),
            "Producto": (["PK id:int", "+ nombre:String", "+ precio:float", "+ stock:int", "FK categoria_id:int"], ["actualizarStock(cantidad:int):void"]),
            "Categoria": (["PK id:int", "+ nombre:String"], []),
            "Pedido": (["PK id:int", "+ fecha:Date", "+ estado:String", "+ total:float", "FK cliente_id:int"], ["calcularTotal():float"]),
            "DetallePedido": (["PK id:int", "+ cantidad:int", "+ precioUnitario:float", "FK pedido_id:int", "FK producto_id:int"], []),
            "Pago": (["PK id:int", "+ monto:float", "+ metodo:String", "+ fecha:Date", "FK pedido_id:int"], ["confirmar():bool"]),
        },
        "relaciones": [
            ("Cliente", "Pedido", "association", "1", "1..*"),
            ("Pedido", "DetallePedido", "composition", "1", "1..*"),
            ("Producto", "DetallePedido", "association", "1", "0..*"),
            ("Categoria", "Producto", "aggregation", "1", "0..*"),
            ("Pedido", "Pago", "association", "1", "0..*"),
        ],
    },
    "universidad": {
        "nombre": "Universidad",
        "descripcion": "Estudiantes, docentes, materias, inscripciones y calificaciones.",
        "clases": {
            "Estudiante": (["PK id:int", "+ nombre:String", "+ email:String", "+ matricula:String"], []),
            "Docente": (["PK id:int", "+ nombre:String", "+ especialidad:String"], []),
            "Carrera": (["PK id:int", "+ nombre:String"], []),
            "Materia": (["PK id:int", "+ nombre:String", "+ creditos:int", "FK carrera_id:int", "FK docente_id:int"], []),
            "Inscripcion": (["PK id:int", "+ gestion:String", "FK estudiante_id:int", "FK materia_id:int"], []),
            "Calificacion": (["PK id:int", "+ nota:float", "+ tipo:String", "FK inscripcion_id:int"], ["aprobado():bool"]),
        },
        "relaciones": [
            ("Carrera", "Materia", "composition", "1", "1..*"),
            ("Docente", "Materia", "association", "1", "0..*"),
            ("Estudiante", "Inscripcion", "association", "1", "0..*"),
            ("Materia", "Inscripcion", "association", "1", "0..*"),
            ("Inscripcion", "Calificacion", "composition", "1", "0..*"),
        ],
    },
    "hospital": {
        "nombre": "Hospital / Salud",
        "descripcion": "Pacientes, médicos, citas, historia clínica y recetas.",
        "clases": {
            "Paciente": (["PK id:int", "+ nombre:String", "+ ci:String", "+ fechaNacimiento:Date"], []),
            "Medico": (["PK id:int", "+ nombre:String", "FK especialidad_id:int"], []),
            "Especialidad": (["PK id:int", "+ nombre:String"], []),
            "Cita": (["PK id:int", "+ fecha:Date", "+ estado:String", "FK paciente_id:int", "FK medico_id:int"], ["cancelar():void"]),
            "HistoriaClinica": (["PK id:int", "+ diagnostico:String", "+ fecha:Date", "FK paciente_id:int"], []),
            "Receta": (["PK id:int", "+ medicamento:String", "+ dosis:String", "FK cita_id:int"], []),
        },
        "relaciones": [
            ("Especialidad", "Medico", "aggregation", "1", "0..*"),
            ("Paciente", "Cita", "association", "1", "0..*"),
            ("Medico", "Cita", "association", "1", "0..*"),
            ("Paciente", "HistoriaClinica", "composition", "1", "0..*"),
            ("Cita", "Receta", "composition", "1", "0..*"),
        ],
    },
    "biblioteca": {
        "nombre": "Biblioteca",
        "descripcion": "Libros, autores, ejemplares, socios y préstamos.",
        "clases": {
            "Libro": (["PK id:int", "+ titulo:String", "+ isbn:String", "+ anio:int"], []),
            "Autor": (["PK id:int", "+ nombre:String", "+ nacionalidad:String"], []),
            "Ejemplar": (["PK id:int", "+ codigo:String", "+ estado:String", "FK libro_id:int"], ["estaDisponible():bool"]),
            "Socio": (["PK id:int", "+ nombre:String", "+ email:String"], []),
            "Prestamo": (["PK id:int", "+ fechaPrestamo:Date", "+ fechaDevolucion:Date", "FK socio_id:int", "FK ejemplar_id:int"], ["devolver():void"]),
        },
        "relaciones": [
            ("Autor", "Libro", "association", "1..*", "1..*"),
            ("Libro", "Ejemplar", "composition", "1", "1..*"),
            ("Socio", "Prestamo", "association", "1", "0..*"),
            ("Ejemplar", "Prestamo", "association", "1", "0..*"),
        ],
    },
}


def _atributo(i: int, texto: str) -> Dict[str, Any]:
    vis, resto = texto.split(" ", 1)
    nombre, tipo = resto.split(":", 1)
    return {"id": f"a{i}", "visibilidad": vis, "nombre": nombre, "tipo": tipo, "version": 0}


def _metodo(i: int, texto: str) -> Dict[str, Any]:
    nombre, resto = texto.split("(", 1)
    params, retorno = resto.split("):", 1)
    return {"id": f"m{i}", "visibilidad": "+", "nombre": nombre, "parametros": params, "retorno": retorno, "version": 0}


def _lienzo(clave: str) -> Dict[str, Any]:
    d = _BASE[clave]
    nodes: List[Dict[str, Any]] = []
    ids: Dict[str, str] = {}
    for idx, (nombre, (attrs, mets)) in enumerate(d["clases"].items()):
        nid = f"{clave}_{nombre.lower()}"
        ids[nombre] = nid
        nodes.append({
            "id": nid, "type": "class", "nombre": nombre, "color": COLOR,
            "x": 80 + (idx % 3) * 320, "y": 80 + (idx // 3) * 300, "width": 220,
            "atributos": [_atributo(i, a) for i, a in enumerate(attrs)],
            "metodos": [_metodo(i, m) for i, m in enumerate(mets)],
            "version": 0, "hash": "", "responsable": "", "responsabilidades": [],
        })
    relations = [
        {"id": f"{clave}_r{i}", "type": t, "sourceId": ids[a], "targetId": ids[b],
         "sourceLabel": sl, "label": tl, "version": 0, "hash": ""}
        for i, (a, b, t, sl, tl) in enumerate(d["relaciones"])
    ]
    return {"nodes": nodes, "relations": relations}


def listar_base() -> List[Dict[str, Any]]:
    return [
        {"id": f"base:{k}", "nombre": v["nombre"], "descripcion": v["descripcion"],
         "clases": len(v["clases"]), "origen": "base"}
        for k, v in _BASE.items()
    ]


def obtener_base(clave: str) -> Dict[str, Any] | None:
    if clave not in _BASE:
        return None
    d = _BASE[clave]
    return {"id": f"base:{clave}", "nombre": d["nombre"], "descripcion": d["descripcion"],
            "clases": len(d["clases"]), "origen": "base", "lienzo": _lienzo(clave)}
