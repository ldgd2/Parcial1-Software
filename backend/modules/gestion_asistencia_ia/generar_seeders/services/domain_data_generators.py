import random
import re
import uuid
from typing import Any, Dict, List, Optional
from faker import Faker

fake = Faker("es_ES")

MATERIAS_UAGRM = [
    ("Programación I", "INF110", 4),
    ("Estructuras de Datos", "INF210", 5),
    ("Bases de Datos I", "INF312", 5),
    ("Bases de Datos II", "INF323", 5),
    ("Sistemas Operativos", "INF314", 4),
    ("Arquitectura de Software", "INF412", 5),
    ("Redes de Computadoras", "INF414", 4),
    ("Seguridad Informática", "INF423", 4),
    ("Inteligencia Artificial", "INF428", 5),
    ("Ingeniería de Software I", "INF220", 5),
    ("Ingeniería de Software II", "INF320", 5),
    ("Sistemas de Información", "INF342", 4),
    ("Cálculo I", "MAT101", 5),
    ("Cálculo II", "MAT102", 5),
    ("Álgebra Lineal", "MAT103", 4),
    ("Física I", "FIS100", 4),
    ("Compiladores", "INF418", 4)
]

CARRERAS_UAGRM = [
    "Ingeniería Informática",
    "Ingeniería de Sistemas",
    "Ciencias de la Computación",
    "Ingeniería en Redes y Telecomunicaciones"
]

MOTIVOS_RETIRO = [
    "Cruce de horario con otra asignatura",
    "Incompatibilidad con horario laboral",
    "Problemas de salud certificados",
    "Ajuste de carga académica semestral",
    "Cambio de modalidad o grupo"
]

EVALUACIONES_PARCIALES = [
    "Primer Examen Parcial",
    "Segundo Examen Parcial",
    "Examen Final Teórico",
    "Proyecto Práctico Final",
    "Evaluación de Laboratorio",
    "Segunda Instancia"
]

GRUPOS_UAGRM = ["SA", "SB", "SC", "SD", "Z1", "Z2", "SX"]
AULAS_UAGRM = ["Aula 236-04", "Aula 212-08", "Lab Cómputo 1", "Lab Cómputo 2", "Auditorio Central"]
ROLES_SISTEMA = ["ESTUDIANTE", "DOCENTE", "ADMINISTRADOR", "JEFE_CARRERA", "AUXILIAR"]
ESTADOS_INSCRIPCION = ["INSCRITO", "APROBADO", "REPROBADO", "RETIRADO", "EN_CURSO"]
METODOS_PAGO = ["QR_SIMPLE", "TRANSFERENCIA_BANCARIA", "TARJETA_DEBITO", "EFECTIVO"]


def resolver_fk_parent(
    col_name: str,
    col_type: str,
    parent_ids_map: Dict[str, List[Any]]
) -> Any:
    c_lower = col_name.lower().lstrip("*")
    cand = re.sub(r"(_id|id)$", "", c_lower)

    matched_ids: Optional[List[Any]] = None
    for k, ids in parent_ids_map.items():
        k_low = k.lower()
        if (
            k_low == cand
            or k_low == f"{cand}s"
            or k_low == f"{cand}es"
            or (cand.endswith("s") and k_low == cand[:-1])
        ):
            matched_ids = ids
            break

    if matched_ids and len(matched_ids) > 0:
        return random.choice(matched_ids)

    # Si no se encuentra tabla padre, generar valor acorde al tipo
    if "uuid" in col_type or col_type == "string":
        return str(uuid.uuid4())
    return random.randint(1, 10)


def generar_valor_campo(
    col_name: str,
    col_type: str,
    record_idx: int,
    parent_ids_map: Dict[str, List[Any]],
    table_name: str,
    es_fk: bool = False
) -> Any:
    """Genera datos coherentes y randomizados mediante Faker y librerías nativas."""
    c_lower = col_name.lower().lstrip("*")
    t_lower = table_name.lower()

    # 1. Claves Foráneas
    if es_fk or c_lower.endswith("_id") or (c_lower.endswith("id") and c_lower != "id"):
        return resolver_fk_parent(col_name, col_type, parent_ids_map)

    # 2. Clave Primaria ID explícita
    if c_lower == "id":
        if col_type in ["int", "integer", "bigint", "long", "#"]:
            return record_idx + 1
        return str(uuid.uuid4())

    # 3. Dominio Académico (UAGRM / Materias / Notas / Parciales / Retiros)
    if any(k in c_lower for k in ["sigla", "codigo_materia", "cod_materia"]):
        materia_info = MATERIAS_UAGRM[record_idx % len(MATERIAS_UAGRM)]
        return materia_info[1]

    if c_lower in ["materia", "asignatura"] or ("nombre" in c_lower and "materia" in t_lower):
        materia_info = MATERIAS_UAGRM[record_idx % len(MATERIAS_UAGRM)]
        return materia_info[0]

    if "credito" in c_lower:
        materia_info = MATERIAS_UAGRM[record_idx % len(MATERIAS_UAGRM)]
        return materia_info[2]

    if any(k in c_lower for k in ["parcial", "evaluacion", "tipo_examen"]):
        return EVALUACIONES_PARCIALES[record_idx % len(EVALUACIONES_PARCIALES)]

    if any(k in c_lower for k in ["nota", "calificacion", "puntaje", "score", "ponderacion"]):
        if "ponderacion" in c_lower:
            return random.choice([20.0, 25.0, 30.0, 40.0])
        # Calificación numérica coherente (distribución entre aprobados y reprobados)
        return round(random.uniform(40.0, 99.5), 2)

    if any(k in c_lower for k in ["motivo", "razon", "causa"]) and "retiro" in t_lower:
        return MOTIVOS_RETIRO[record_idx % len(MOTIVOS_RETIRO)]

    if "carrera" in c_lower or ("nombre" in c_lower and "carrera" in t_lower):
        return CARRERAS_UAGRM[record_idx % len(CARRERAS_UAGRM)]

    if "semestre" in c_lower or "periodo" in c_lower:
        if col_type in ["int", "integer"]:
            return (record_idx % 10) + 1
        return f"{(record_idx % 2) + 1}-2026"

    if "gestion" in c_lower or "anio" in c_lower or "año" in c_lower:
        return random.choice([2024, 2025, 2026])

    if "grupo" in c_lower:
        return random.choice(GRUPOS_UAGRM)

    if "aula" in c_lower or "salon" in c_lower or "laboratorio" in c_lower:
        return random.choice(AULAS_UAGRM)

    if any(k in c_lower for k in ["matricula", "registro", "nro_registro"]):
        return f"2{random.randint(19, 26)}{random.randint(100000, 999999)}"

    # 4. Datos de Personas y Usuarios
    if c_lower in ["email", "correo", "mail"]:
        first = fake.first_name().lower()
        last = fake.last_name().lower()
        return f"{first}.{last}{random.randint(10, 99)}@uagrm.edu.bo"

    if c_lower in ["first_name", "primer_nombre"]:
        return fake.first_name()

    if c_lower in ["last_name", "apellido", "paterno", "materno"]:
        return fake.last_name()

    if any(k in c_lower for k in ["nombre_completo", "full_name"]) or (
        "nombre" in c_lower and any(p in t_lower for p in ["usuario", "estudiante", "alumno", "docente", "persona", "cliente"])
    ):
        return f"{fake.first_name()} {fake.last_name()} {fake.last_name()}"

    if any(k in c_lower for k in ["telefono", "celular", "phone", "movil"]):
        return f"+591 {random.choice([6, 7])}{random.randint(1000000, 9999999)}"

    if any(k in c_lower for k in ["ci", "dni", "cedula", "identificacion"]):
        return f"{random.randint(4000000, 11000000)} SC"

    if any(k in c_lower for k in ["password", "clave", "contrasena", "contraseña"]):
        return "$2a$10$eO1dFjZ6wYwN8Y8B9WzI6O.D0.rYw8c9YqXpX4O.d0.rYw8c9YqXp"

    if c_lower in ["username", "usuario", "login"]:
        return f"{fake.user_name()}_{random.randint(100, 999)}"

    if c_lower in ["rol", "role", "tipo_usuario"]:
        return random.choice(ROLES_SISTEMA)

    # 5. Comercio y Finanzas
    if any(k in c_lower for k in ["precio", "costo", "tarifa"]):
        return round(random.uniform(20.0, 480.0), 2)

    if any(k in c_lower for k in ["monto", "total", "subtotal", "saldo"]):
        return round(random.uniform(50.0, 1500.0), 2)

    if any(k in c_lower for k in ["stock", "cantidad", "unidades", "cupo", "cupos"]):
        return random.randint(15, 60)

    if any(k in c_lower for k in ["metodo_pago", "forma_pago"]):
        return random.choice(METODOS_PAGO)

    # 6. Estados y Banderas
    if any(k in c_lower for k in ["estado", "status"]):
        if any(w in t_lower for w in ["inscripcion", "materia", "alumno", "parcial"]):
            return random.choice(ESTADOS_INSCRIPCION)
        return random.choice(["ACTIVO", "PENDIENTE", "FINALIZADO"])

    if col_type in ["bool", "boolean", "?"] or c_lower.startswith("es_") or c_lower.startswith("is_") or "activo" in c_lower or "habilitado" in c_lower:
        return random.choice([True, True, True, False])

    # 7. Fechas y Horas
    if any(k in c_lower for k in ["fecha_nacimiento", "birth_date"]):
        return fake.date_of_birth(minimum_age=18, maximum_age=32).isoformat()

    if "fecha" in c_lower or col_type in ["date", "@"]:
        return fake.date_this_year().isoformat()

    if any(k in c_lower for k in ["hora", "time"]):
        return f"{random.randint(7, 21):02d}:{random.choice(['00', '15', '30', '45'])}:00"

    if col_type in ["datetime", "timestamp", "!"] or any(k in c_lower for k in ["created_at", "updated_at"]):
        return fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")

    # 8. Direcciones y Ubicaciones
    if any(k in c_lower for k in ["direccion", "address", "calle"]):
        return fake.street_address()

    if any(k in c_lower for k in ["ciudad", "city"]):
        return random.choice(["Santa Cruz de la Sierra", "La Paz", "Cochabamba", "Tarija", "Sucre"])

    if any(k in c_lower for k in ["pais", "country"]):
        return "Bolivia"

    # 9. Descripciones o textos
    if any(k in c_lower for k in ["descripcion", "detalle", "observacion", "comentario", "nota_texto"]):
        return fake.sentence(nb_words=10)

    # 10. Fallbacks por tipo
    if col_type in ["int", "integer", "bigint", "long", "#"]:
        return random.randint(10, 500)
    if col_type in ["float", "double", "decimal"]:
        return round(random.uniform(5.0, 100.0), 2)
    if "uuid" in col_type:
        return str(uuid.uuid4())

    return f"{col_name}_{random.randint(100, 999)}"

