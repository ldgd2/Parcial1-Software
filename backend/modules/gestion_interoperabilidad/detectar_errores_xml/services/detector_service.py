import re
from typing import Any, Dict, List, Optional, Set, Tuple
from backend.modules.gestion_interoperabilidad.importar_desde_xml.services.import_service import parsear_xmi
from backend.modules.gestion_interoperabilidad.detectar_errores_xml.schemas.response import (
    DetectarErroresResponse,
    ErrorLogicoBD
)

SQL_RESERVED_WORDS = {
    "user", "order", "group", "table", "select", "insert", "update", "delete",
    "from", "where", "limit", "offset", "join", "inner", "outer", "left", "right",
    "full", "check", "default", "primary", "foreign", "key", "constraint", "index",
    "grant", "revoke", "schema", "database", "view", "trigger", "procedure", "function",
    "values", "into", "as", "by", "having", "union", "all", "distinct", "case", "when"
}

NON_TABLE_TYPES = {
    "note", "text", "requirement", "package", "boundary", "port", "expose_interface", "issue", "change"
}


def _extraer_nombre_tipo_attr(raw_attr: Any) -> Tuple[str, str, bool]:
    """Retorna (nombre_columna, tipo_dato, es_fk)."""
    if isinstance(raw_attr, dict):
        nombre = str(raw_attr.get("nombre") or raw_attr.get("name") or "").strip()
        tipo = str(raw_attr.get("tipo") or raw_attr.get("type") or "string").strip().lower()
        es_fk = raw_attr.get("visibilidad") == "FK" or nombre.startswith("*") or nombre.lower().endswith("_id")
        return nombre.lstrip("+*-#"), tipo, es_fk

    attr_str = str(raw_attr).strip()
    es_fk = attr_str.startswith("*") or "FK" in attr_str or "_id" in attr_str.lower()
    clean = attr_str.lstrip("+*-# ")

    if ":" in clean:
        parts = clean.split(":", 1)
        name = parts[0].strip()
        dtype = parts[1].strip().lower()
    else:
        name = clean
        dtype = "string"

    return name, dtype, es_fk


def _tiene_pk(node: Dict[str, Any]) -> bool:
    attrs = node.get("attributes") or node.get("atributos") or []
    for a in attrs:
        name, dtype, es_fk = _extraer_nombre_tipo_attr(a)
        if not es_fk and (name.lower() == "id" or name.lower().startswith("id_") or "pk" in dtype):
            return True
    return False


def _obtener_tipo_pk(node: Dict[str, Any]) -> str:
    attrs = node.get("attributes") or node.get("atributos") or []
    for a in attrs:
        name, dtype, es_fk = _extraer_nombre_tipo_attr(a)
        if not es_fk and (name.lower() == "id" or name.lower().startswith("id_")):
            return dtype
    return "int"


async def analizar_errores_logicos_bd(
    xml_content: Optional[str] = None,
    nodes: Optional[List[Dict[str, Any]]] = None,
    relations: Optional[List[Dict[str, Any]]] = None
) -> DetectarErroresResponse:
    if (not nodes or len(nodes) == 0) and xml_content:
        parsed = await parsear_xmi(xml_content)
        nodes = parsed.get("nodes", [])
        relations = parsed.get("relations", [])

    nodes = nodes or []
    relations = relations or []

    errores: List[ErrorLogicoBD] = []
    error_idx = 1

    table_map: Dict[str, Dict[str, Any]] = {}
    table_names_lower: Dict[str, str] = {}
    connected_tables: Set[str] = set()

    for n in nodes:
        name = str(n.get("name") or n.get("nombre") or "").strip()
        n_id = str(n.get("id") or name).strip()
        if not name:
            continue
        table_map[n_id] = n
        table_map[name] = n
        table_names_lower[name.lower()] = name
        table_names_lower[n_id.lower()] = name

    # 1. Regla: Palabra reservada en el nombre de la tabla
    for n in nodes:
        node_type = str(n.get("type") or n.get("tipo") or "class").lower()
        if node_type in NON_TABLE_TYPES:
            continue
        t_name = str(n.get("name") or n.get("nombre") or "").strip()
        if not t_name:
            continue
        if t_name.lower() in SQL_RESERVED_WORDS:
            errores.append(ErrorLogicoBD(
                id=f"ERR-{error_idx}",
                tipo="palabra_reservada",
                severidad="alta",
                tabla=t_name,
                columna=None,
                descripcion=f"La tabla '{t_name}' usa una palabra reservada de PostgreSQL/SQL estándar. Provocará fallos de sintaxis en DDL.",
                solucion_sugerida=f"Renombrar la entidad a '{t_name.capitalize()}Entity' o '{t_name.capitalize()}Record' o '{t_name}s'."
            ))
            error_idx += 1

        # 2. Regla: Sin Clave Primaria (PK)
        if not _tiene_pk(n):
            errores.append(ErrorLogicoBD(
                id=f"ERR-{error_idx}",
                tipo="sin_pk",
                severidad="alta",
                tabla=t_name,
                columna="id",
                descripcion=f"La tabla '{t_name}' carece de una clave primaria (PK). Todo modelo relacional requiere una columna identificadora única.",
                solucion_sugerida=f"Agregar el atributo identificador '+id:int' a la tabla '{t_name}'."
            ))
            error_idx += 1

        # Inspección de atributos y FKs declarados en la tabla
        attrs = n.get("attributes") or n.get("atributos") or []
        for a in attrs:
            a_name, a_type, es_fk = _extraer_nombre_tipo_attr(a)

            # Palabra reservada en columna
            if a_name.lower() in SQL_RESERVED_WORDS:
                errores.append(ErrorLogicoBD(
                    id=f"ERR-{error_idx}",
                    tipo="palabra_reservada",
                    severidad="media",
                    tabla=t_name,
                    columna=a_name,
                    descripcion=f"La columna '{a_name}' en la tabla '{t_name}' coincide con la palabra reservada SQL '{a_name.upper()}'.",
                    solucion_sugerida=f"Renombrar el atributo a '{a_name}_val' o utilizar un término de dominio más explícito."
                ))
                error_idx += 1

            # Detección de FK huérfana por convención de nombre (*target_id o similar)
            if es_fk or a_name.lower().endswith("_id"):
                ref_candidate = re.sub(r"_id$", "", a_name.lower()).lstrip("*")
                # Buscar si existe la tabla referenciada
                matched_target = None
                for candidate_key in [ref_candidate, f"{ref_candidate}s", f"{ref_candidate}es"]:
                    if candidate_key in table_names_lower:
                        matched_target = table_names_lower[candidate_key]
                        break

                if not matched_target:
                    errores.append(ErrorLogicoBD(
                        id=f"ERR-{error_idx}",
                        tipo="fk_huerfana",
                        severidad="alta",
                        tabla=t_name,
                        columna=a_name,
                        descripcion=f"La clave foránea '{a_name}' en la tabla '{t_name}' apunta a una entidad inexistente '{ref_candidate}'.",
                        solucion_sugerida=f"Crear la entidad referenciada '{ref_candidate.capitalize()}' o corregir el nombre de la relación."
                    ))
                    error_idx += 1
                else:
                    connected_tables.add(t_name.lower())
                    connected_tables.add(matched_target.lower())
                    # Tipo discordante entre FK y PK de destino
                    target_node = table_map.get(matched_target)
                    if target_node:
                        target_pk_type = _obtener_tipo_pk(target_node)
                        if a_type != "fk" and a_type != target_pk_type and not (a_type in ["int", "integer", "bigint"] and target_pk_type in ["int", "integer", "bigint"]):
                            errores.append(ErrorLogicoBD(
                                id=f"ERR-{error_idx}",
                                tipo="tipo_discordante",
                                severidad="media",
                                tabla=t_name,
                                columna=a_name,
                                descripcion=f"La columna FK '{a_name}' es de tipo '{a_type}', pero la PK de la tabla destino '{matched_target}' es de tipo '{target_pk_type}'.",
                                solucion_sugerida=f"Modificar el tipo de '{a_name}' en '{t_name}' a '{target_pk_type}' para coincidir con la clave primaria."
                            ))
                            error_idx += 1

    # 3. Análisis de Relaciones Explícitas del Diagrama
    fks_graph: Dict[str, Set[str]] = {}

    for r in relations:
        s_id = str(r.get("sourceId") or r.get("source") or "").strip()
        t_id = str(r.get("targetId") or r.get("target") or "").strip()
        r_type = str(r.get("type") or "association").lower().strip()
        r_label = str(r.get("label") or "").strip().lower()

        s_node = table_map.get(s_id)
        t_node = table_map.get(t_id)

        s_name = str(s_node.get("name") or s_node.get("nombre") or s_id) if s_node else s_id
        t_name = str(t_node.get("name") or t_node.get("nombre") or t_id) if t_node else t_id

        # FK Huérfana en relación: target o source no existen
        if not s_node:
            errores.append(ErrorLogicoBD(
                id=f"ERR-{error_idx}",
                tipo="fk_huerfana",
                severidad="alta",
                tabla=s_id,
                columna=None,
                descripcion=f"La relación nace en un elemento origen '{s_id}' que no está presente en las tablas del modelo.",
                solucion_sugerida=f"Eliminar la relación huérfana o instanciar la clase '{s_id}'."
            ))
            error_idx += 1
            continue

        if not t_node:
            errores.append(ErrorLogicoBD(
                id=f"ERR-{error_idx}",
                tipo="fk_huerfana",
                severidad="alta",
                tabla=s_name,
                columna=t_id,
                descripcion=f"La relación desde '{s_name}' apunta a un destino '{t_id}' que no existe en el diagrama.",
                solucion_sugerida=f"Crear la tabla de destino '{t_id}' o desvincular la relación."
            ))
            error_idx += 1
            continue

        connected_tables.add(s_name.lower())
        connected_tables.add(t_name.lower())

        # Registrar grafo para dependencias circulares
        if s_name not in fks_graph:
            fks_graph[s_name] = set()
        fks_graph[s_name].add(t_name)

        # 4. Relación Muchos a Muchos Directa (N:M)
        if "n:m" in r_label or r_type in ["n:m", "many_to_many"] or ("*" in r_label and ".." in r_label and r_label.count("*") >= 2):
            errores.append(ErrorLogicoBD(
                id=f"ERR-{error_idx}",
                tipo="relacion_nm_directa",
                severidad="alta",
                tabla=s_name,
                columna=f"Relación N:M con {t_name}",
                descripcion=f"Existe una relación muchos a muchos (N:M) directa entre '{s_name}' y '{t_name}'. Las bases de datos relacionales no soportan N:M directo.",
                solucion_sugerida=f"Crear una tabla intermedia/asociativa '{s_name}_{t_name}' que contenga las dos claves foráneas correspondientes."
            ))
            error_idx += 1

    # 5. Dependencias Circulares Directas (A -> B y B -> A)
    pares_verificados = set()
    for tabla_a, destinos in fks_graph.items():
        for tabla_b in destinos:
            if tabla_b in fks_graph and tabla_a in fks_graph[tabla_b]:
                par = tuple(sorted([tabla_a, tabla_b]))
                if par not in pares_verificados:
                    pares_verificados.add(par)
                    errores.append(ErrorLogicoBD(
                        id=f"ERR-{error_idx}",
                        tipo="dependencia_circular",
                        severidad="alta",
                        tabla=tabla_a,
                        columna=f"Ciclo con {tabla_b}",
                        descripcion=f"Dependencia circular directa detectada entre '{tabla_a}' y '{tabla_b}'. Impedirá inserciones atómicas sin deshabilitar restricciones.",
                        solucion_sugerida=f"Convertir una de las claves foráneas en nullable o extraer la relación cruzada a una tabla intermedia."
                    ))
                    error_idx += 1

    # 6. Tablas Aisladas (cero conexiones)
    for n in nodes:
        node_type = str(n.get("type") or n.get("tipo") or "class").lower()
        if node_type in NON_TABLE_TYPES:
            continue
        name = str(n.get("name") or n.get("nombre") or "").strip()
        if not name:
            continue
        if name.lower() not in connected_tables:
            errores.append(ErrorLogicoBD(
                id=f"ERR-{error_idx}",
                tipo="tabla_aislada",
                severidad="media",
                tabla=name,
                columna=None,
                descripcion=f"La tabla '{name}' se encuentra totalmente aislada (sin relaciones ni claves foráneas conectadas a otras entidades).",
                solucion_sugerida=f"Conectar '{name}' a la entidad aggregate root o módulo del dominio al que pertenece."
            ))
            error_idx += 1

    stats: Dict[str, int] = {}
    for err in errores:
        stats[err.tipo] = stats.get(err.tipo, 0) + 1

    resumen_text = (
        f"Se detectaron {len(errores)} inconsistencias lógicas en el diseño de base de datos."
        if errores
        else "El diseño de base de datos es 100% consistente y válido para generación relacional."
    )

    return DetectarErroresResponse(
        total_errores=len(errores),
        es_valido=len(errores) == 0,
        errores=errores,
        estadisticas=stats,
        resumen=resumen_text
    )

