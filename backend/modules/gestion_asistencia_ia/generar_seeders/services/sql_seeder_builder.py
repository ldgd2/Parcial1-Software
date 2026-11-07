import re
import uuid
from typing import Any, Dict, List, Tuple
from backend.modules.gestion_asistencia_ia.generar_seeders.services.topological_sorter import extraer_info_columna
from backend.modules.gestion_asistencia_ia.generar_seeders.services.domain_data_generators import generar_valor_campo


def sanitizar_nombre_tabla(nombre_crudo: str) -> str:
    """Normaliza el nombre a minúsculas pluralizado acorde a Spring Boot y JPA."""
    limpio = re.sub(r"[^a-zA-Z0-9_]", "_", str(nombre_crudo)).strip("_").lower()
    if not limpio:
        limpio = "entidad"
    if not limpio.endswith("s"):
        limpio = f"{limpio}s"
    return limpio


def formatear_valor_sql(val: Any) -> str:
    """Escapa y formatea valores para sentencias SQL estándar."""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    val_str = str(val).replace("'", "''")
    return f"'{val_str}'"


def construir_seeders_sql(
    orden_tablas: List[Dict[str, Any]],
    cantidad_por_tabla: int = 10
) -> Tuple[str, Dict[str, List[Any]], Dict[str, int], int]:
    """
    Construye las sentencias SQL con integridad referencial e idempotencia
    mediante ON CONFLICT (id) DO NOTHING para PostgreSQL / Spring Boot.
    """
    parent_ids_map: Dict[str, List[Any]] = {}
    registros_por_tabla: Dict[str, int] = {}
    total_registros = 0

    sql_lines = [
        "-- ===========================================================================",
        "-- SEEDERS DE PRUEBA GENERADOS AUTOMÁTICAMENTE PARA SPRING BOOT / POSTGRESQL",
        f"-- Registros generados por tabla: {cantidad_por_tabla}",
        "-- Integridad Referencial: Garantizada por Ordenamiento Topológico",
        "-- Idempotencia: ON CONFLICT (id) DO NOTHING",
        "-- ===========================================================================\n",
        "BEGIN;\n"
    ]

    for node in orden_tablas:
        t_name = str(node.get("name") or node.get("nombre") or "").strip()
        if not t_name:
            continue

        table_sql_name = sanitizar_nombre_tabla(t_name)
        attrs = node.get("attributes") or node.get("atributos") or []

        # Extraer información de columnas
        columnas_info: List[Tuple[str, str, bool]] = []
        has_id = False
        has_created_at = False
        has_updated_at = False
        has_is_active = False

        for a in attrs:
            c_name, c_type, es_fk = extraer_info_columna(a)
            c_low = c_name.lower().lstrip("*")
            if c_low == "id":
                has_id = True
                columnas_info.insert(0, (c_name, c_type, es_fk))
            elif c_low in ["created_at", "createdat"]:
                has_created_at = True
                columnas_info.append((c_name, c_type, es_fk))
            elif c_low in ["updated_at", "updatedat"]:
                has_updated_at = True
                columnas_info.append((c_name, c_type, es_fk))
            elif c_low in ["is_active", "isactive"]:
                has_is_active = True
                columnas_info.append((c_name, c_type, es_fk))
            else:
                columnas_info.append((c_name, c_type, es_fk))

        # Garantizar compatibilidad con BaseEntity de Spring Boot
        if not has_id:
            columnas_info.insert(0, ("id", "uuid", False))
        if not has_created_at:
            columnas_info.append(("created_at", "timestamp", False))
        if not has_updated_at:
            columnas_info.append(("updated_at", "timestamp", False))
        if not has_is_active:
            columnas_info.append(("is_active", "boolean", False))

        generated_ids: List[Any] = []
        sql_lines.append(f"-- Población de datos para la entidad '{t_name}' (Tabla: {table_sql_name})")

        col_names = [f'"{re.sub(r"[^a-zA-Z0-9_]", "_", c[0].lower().lstrip("*"))}"' for c in columnas_info]
        cols_header = ", ".join(col_names)

        for i in range(cantidad_por_tabla):
            row_values: List[str] = []
            current_row_id: Any = None

            for col_name, col_type, es_fk in columnas_info:
                c_low = col_name.lower().lstrip("*")
                if c_low == "id":
                    val = current_row_id or generar_valor_campo(col_name, col_type, i, parent_ids_map, t_name, es_fk)
                    current_row_id = val
                else:
                    val = generar_valor_campo(col_name, col_type, i, parent_ids_map, t_name, es_fk)

                row_values.append(formatear_valor_sql(val))

            if current_row_id is not None:
                generated_ids.append(current_row_id)

            vals_str = ", ".join(row_values)
            sql_lines.append(
                f"INSERT INTO {table_sql_name} ({cols_header}) VALUES ({vals_str}) ON CONFLICT (id) DO NOTHING;"
            )

        # Registrar IDs generados para que las tablas dependientes los usen como FKs
        parent_ids_map[t_name] = generated_ids
        parent_ids_map[t_name.lower()] = generated_ids
        parent_ids_map[table_sql_name] = generated_ids
        if t_name.lower().endswith("s"):
            parent_ids_map[t_name.lower()[:-1]] = generated_ids

        registros_por_tabla[t_name] = cantidad_por_tabla
        total_registros += cantidad_por_tabla
        sql_lines.append("")

    sql_lines.append("COMMIT;\n")
    final_sql = "\n".join(sql_lines)

    return final_sql, parent_ids_map, registros_por_tabla, total_registros

