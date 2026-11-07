import random
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from backend.modules.gestion_asistencia_ia.generar_seeders.schemas.response import GenerarSeedersResponse

NOMBRES_EJEMPLO = [
    "Alejandro Morales", "Valentina Flores", "Santiago Rojas", "Camila Quispe",
    "Mateo Mamani", "Luciana Choque", "Sebastián Mendoza", "Isabella Vargas",
    "Nicolás Torrez", "Mariana Ríos", "Daniel Castro", "Sofía Fernández",
    "Gabriel Gutiérrez", "Valeria Pinto", "Joaquín Soliz", "Natalia Miranda",
    "Diego Navarro", "Elena Romero", "Rodrigo Cáceres", "Adriana Benítez"
]

CARRERAS = [
    "Ingeniería de Sistemas", "Ingeniería Informática", "Ingeniería de Software",
    "Ciencias de la Computación", "Ingeniería en Redes y Telecomunicaciones"
]

MATERIAS = [
    "Programación I", "Estructuras de Datos", "Bases de Datos I",
    "Ingeniería de Software I", "Sistemas Operativos", "Arquitectura de Software",
    "Redes de Computadoras", "Seguridad Informática", "Inteligencia Artificial"
]


def _extraer_info_columna(raw_attr: Any) -> Tuple[str, str, bool]:
    """Retorna (nombre_columna, tipo_sql, es_fk)."""
    if isinstance(raw_attr, dict):
        nombre = str(raw_attr.get("nombre") or raw_attr.get("name") or "").strip().lstrip("+*-# ")
        tipo = str(raw_attr.get("tipo") or raw_attr.get("type") or "string").strip().lower()
        es_fk = raw_attr.get("visibilidad") == "FK" or nombre.startswith("*") or nombre.lower().endswith("_id")
        return nombre, tipo, es_fk

    raw_str = str(raw_attr).strip()
    es_fk = raw_str.startswith("*") or "FK" in raw_str or "_id" in raw_str.lower()
    clean = raw_str.lstrip("+*-# ")
    if ":" in clean:
        parts = clean.split(":", 1)
        name = parts[0].strip()
        dtype = parts[1].strip().lower()
    else:
        name = clean
        dtype = "string"
    return name, dtype, es_fk


def _orden_topologico_tablas(nodes: List[Dict[str, Any]], relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ordena las entidades para que las tablas maestras sin FKs se inserten primero."""
    table_by_name = {}
    table_by_id = {}
    for n in nodes:
        name = str(n.get("name") or n.get("nombre") or "").strip()
        n_id = str(n.get("id") or name).strip()
        if name:
            table_by_name[name] = n
            table_by_name[name.lower()] = n
            table_by_id[n_id] = n
            table_by_id[n_id.lower()] = n

    # Construir grafo de dependencias: A depende de B si A tiene FK hacia B
    dependencias = defaultdict(set)
    grados_entrada = defaultdict(int)

    for n in nodes:
        t_name = str(n.get("name") or n.get("nombre") or "").strip()
        if not t_name:
            continue
        grados_entrada[t_name] = 0

    for n in nodes:
        t_name = str(n.get("name") or n.get("nombre") or "").strip()
        attrs = n.get("attributes") or n.get("atributos") or []
        for a in attrs:
            col_name, _, es_fk = _extraer_info_columna(a)
            if es_fk or col_name.lower().endswith("_id"):
                cand = re.sub(r"_id$", "", col_name.lower()).lstrip("*")
                if cand in table_by_name and table_by_name[cand]["name"] != t_name:
                    parent_name = table_by_name[cand]["name"]
                    dependencias[parent_name].add(t_name)

    # También analizar relaciones UML (composición o asociación dirigida)
    for r in relations:
        s_id = str(r.get("sourceId") or r.get("source") or "").strip()
        t_id = str(r.get("targetId") or r.get("target") or "").strip()
        s_node = table_by_id.get(s_id.lower())
        t_node = table_by_id.get(t_id.lower())
        if s_node and t_node and s_node != t_node:
            s_name = s_node.get("name") or s_node.get("nombre")
            t_name = t_node.get("name") or t_node.get("nombre")
            # En herencia: hijo depende de padre
            if r.get("type") == "inheritance":
                dependencias[t_name].add(s_name)
            elif r.get("type") in ["composition", "association"]:
                dependencias[s_name].add(t_name)

    # Calcular grados de entrada
    for parent, hijos in dependencias.items():
        for hijo in hijos:
            grados_entrada[hijo] += 1

    cola = deque([t for t, g in grados_entrada.items() if g == 0])
    orden = []

    while cola:
        curr = cola.popleft()
        if curr in table_by_name:
            orden.append(table_by_name[curr])
        for hijo in dependencias[curr]:
            grados_entrada[hijo] -= 1
            if grados_entrada[hijo] == 0:
                cola.append(hijo)

    # Agregar tablas que no hayan entrado en la cola (ej. por ciclos)
    agregadas = {str(n.get("name") or n.get("nombre")) for n in orden}
    for n in nodes:
        n_name = str(n.get("name") or n.get("nombre"))
        if n_name and n_name not in agregadas:
            orden.append(n)
            agregadas.add(n_name)

    return orden


def _generar_valor_columna(
    col_name: str,
    col_type: str,
    registro_idx: int,
    parent_ids_map: Dict[str, List[int]],
    tabla_nombre: str
) -> Any:
    c_lower = col_name.lower().lstrip("*")

    # Claves Foráneas (FK)
    if c_lower.endswith("_id") or "fk" in col_type:
        parent_table_cand = re.sub(r"_id$", "", c_lower)
        # Buscar lista de IDs generados para el padre
        matched_ids = None
        for k, ids in parent_ids_map.items():
            if k.lower() == parent_table_cand or k.lower() == f"{parent_table_cand}s":
                matched_ids = ids
                break

        if matched_ids and len(matched_ids) > 0:
            return matched_ids[registro_idx % len(matched_ids)]
        return 1

    # Nombres de personas
    if "nombre" in c_lower and "usuario" in tabla_nombre.lower() or c_lower in ["estudiante", "docente", "autor", "usuario"]:
        return NOMBRES_EJEMPLO[registro_idx % len(NOMBRES_EJEMPLO)]

    if c_lower in ["nombre", "name", "titulo", "title"]:
        if "curso" in tabla_nombre.lower() or "materia" in tabla_nombre.lower():
            return MATERIAS[registro_idx % len(MATERIAS)]
        return f"{tabla_nombre} {registro_idx + 1}"

    # Correos electrónicos
    if "email" in c_lower or "correo" in c_lower:
        nombre = NOMBRES_EJEMPLO[registro_idx % len(NOMBRES_EJEMPLO)].lower().replace(" ", ".")
        return f"{nombre}{registro_idx + 1}@universidad.edu.bo"

    # Códigos / Matrículas
    if "codigo" in c_lower or "code" in c_lower:
        return f"COD-{(registro_idx + 1) * 101}"
    if "matricula" in c_lower:
        return f"MAT-2026-{(registro_idx + 1):04d}"

    # Passwords
    if "password" in c_lower or "clave" in c_lower:
        return "$2a$10$eO1dFjZ6wYwN8Y8B9WzI6O.D0.rYw8c9YqXpX4O.d0.rYw8c9YqXp"

    # Fechas
    if "fecha" in c_lower or col_type in ["date", "@"]:
        mes = (registro_idx % 11) + 1
        dia = (registro_idx % 27) + 1
        return f"2026-{mes:02d}-{dia:02d}"

    # Timestamps / Datetimes
    if col_type in ["datetime", "timestamp", "!"]:
        mes = (registro_idx % 11) + 1
        dia = (registro_idx % 27) + 1
        return f"2026-{mes:02d}-{dia:02d} 09:30:00"

    # Notas / Ponderaciones / Precios
    if any(k in c_lower for k in ["nota", "calificacion", "puntaje", "score", "ponderacion"]):
        return round(51.0 + ((registro_idx * 7.3) % 49.0), 2)
    if any(k in c_lower for k in ["precio", "monto", "total", "saldo", "credito", "costo"]):
        return round(120.0 + (registro_idx * 45.5), 2)

    # Booleanos
    if col_type in ["bool", "boolean", "?"] or c_lower.startswith("es_") or c_lower.startswith("is_") or "leido" in c_lower or "activo" in c_lower:
        return True if registro_idx % 3 != 0 else False

    # Estados y Roles
    if "rol" in c_lower:
        roles = ["DOCENTE", "ESTUDIANTE", "ADMINISTRADOR"]
        return roles[registro_idx % len(roles)]
    if "estado" in c_lower:
        estados = ["ACTIVO", "PENDIENTE", "FINALIZADO", "APROBADO"]
        return estados[registro_idx % len(estados)]
    if "carrera" in c_lower:
        return CARRERAS[registro_idx % len(CARRERAS)]
    if "semestre" in c_lower:
        return (registro_idx % 8) + 1
    if "gestion" in c_lower:
        return 2026

    # Números enteros
    if col_type in ["int", "integer", "#"]:
        return (registro_idx + 1) * 5

    # Texto general
    return f"{col_name}_{registro_idx + 1}"


def generar_script_seeders(
    nodes: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
    cantidad_por_tabla: int = 10,
    formato: str = "sql"
) -> GenerarSeedersResponse:
    """
    Genera datos coherentes para pruebas relacionales ordenados topológicamente.
    """
    if not nodes:
        return GenerarSeedersResponse(
            resumen="No hay entidades en el diagrama para sembrar.",
            total_tablas=0,
            total_registros=0,
            orden_insercion=[],
            registros_por_tabla={},
            sql_script="-- No hay entidades definidas para generar seeders.\n",
            java_code=None
        )

    orden_tablas = _orden_topologico_tablas(nodes, relations)
    orden_nombres = [str(n.get("name") or n.get("nombre")) for n in orden_tablas]

    parent_ids_map: Dict[str, List[int]] = {}
    registros_por_tabla: Dict[str, int] = {}

    sql_lines = [
        "-- ===========================================================================",
        "-- SEEDERS DE PRUEBA GENERADOS AUTOMÁTICAMENTE (ENTORNO DE DESARROLLO/TEST)",
        f"-- Cantidad de registros por entidad: {cantidad_por_tabla}",
        "-- Integridad Referencial: Respetada por Ordenamiento Topológico",
        "-- ===========================================================================\n",
        "BEGIN;\n"
    ]

    total_registros = 0

    for node in orden_tablas:
        t_name = str(node.get("name") or node.get("nombre") or "").strip()
        if not t_name:
            continue

        table_sql_name = re.sub(r"(?<!^)(?=[A-Z])", "_", t_name).lower()
        if not table_sql_name.endswith("s"):
            table_sql_name = f"{table_sql_name}s"

        attrs = node.get("attributes") or node.get("atributos") or []

        # Extraer columnas excluyendo PK autoincremental de la sentencia si es id
        columnas_info = []
        has_id_pk = False

        for a in attrs:
            c_name, c_type, es_fk = _extraer_info_columna(a)
            if c_name.lower() == "id" and not es_fk:
                has_id_pk = True
                continue
            columnas_info.append((c_name, c_type, es_fk))

        generated_ids = list(range(1, cantidad_por_tabla + 1))
        parent_ids_map[t_name] = generated_ids
        parent_ids_map[t_name.lower()] = generated_ids
        registros_por_tabla[t_name] = cantidad_por_tabla
        total_registros += cantidad_por_tabla

        sql_lines.append(f"-- Sembrado de la entidad '{t_name}' (Tabla: {table_sql_name})")

        # Generar sentencias INSERT por lotes
        col_names_quoted = [f'"{c[0].lower().lstrip("*")}"' for c in columnas_info]
        cols_str = ", ".join(col_names_quoted)

        for i in range(cantidad_por_tabla):
            valores = []
            for col_name, col_type, es_fk in columnas_info:
                val = _generar_valor_columna(col_name, col_type, i, parent_ids_map, t_name)

                if val is None:
                    valores.append("NULL")
                elif isinstance(val, bool):
                    valores.append("TRUE" if val else "FALSE")
                elif isinstance(val, (int, float)):
                    valores.append(str(val))
                else:
                    # Escapar comillas simples
                    val_escaped = str(val).replace("'", "''")
                    valores.append(f"'{val_escaped}'")

            vals_str = ", ".join(valores)
            if cols_str:
                sql_lines.append(f"INSERT INTO {table_sql_name} ({cols_str}) VALUES ({vals_str});")
            else:
                sql_lines.append(f"INSERT INTO {table_sql_name} DEFAULT VALUES;")

        # Ajuste de secuencia PostgreSQL si aplica
        if has_id_pk:
            seq_name = f"{table_sql_name}_id_seq"
            sql_lines.append(f"SELECT setval(pg_get_serial_sequence('{table_sql_name}', 'id'), (SELECT COALESCE(MAX(id), 1) FROM {table_sql_name}));")

        sql_lines.append("")

    sql_lines.append("COMMIT;\n")
    final_sql = "\n".join(sql_lines)

    # Generación opcional de CommandLineRunner para Spring Boot
    java_runner_code = None
    if formato in ["java", "java_runner"]:
        java_runner_code = (
            "package com.universidad.backend.config;\n\n"
            "import org.springframework.boot.CommandLineRunner;\n"
            "import org.springframework.context.annotation.Bean;\n"
            "import org.springframework.context.annotation.Configuration;\n"
            "import org.springframework.jdbc.core.JdbcTemplate;\n\n"
            "@Configuration\n"
            "public class DatabaseSeedRunner {\n\n"
            "    @Bean\n"
            "    public CommandLineRunner initDatabase(JdbcTemplate jdbcTemplate) {\n"
            "        return args -> {\n"
            "            System.out.println(\"Iniciando carga de seeders de prueba...\");\n"
            "            // Ejecutar sentencias generadas\n"
            "        };\n"
            "    }\n"
            "}\n"
        )

    resumen_text = (
        f"Se generaron {total_registros} registros coherentes para {len(orden_tablas)} tablas relacionales, "
        f"respetando el orden de dependencia de claves foráneas."
    )

    return GenerarSeedersResponse(
        resumen=resumen_text,
        total_tablas=len(orden_tablas),
        total_registros=total_registros,
        orden_insercion=orden_nombres,
        registros_por_tabla=registros_por_tabla,
        sql_script=final_sql,
        java_code=java_runner_code
    )

