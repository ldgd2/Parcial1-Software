import re
from typing import Any, Dict, List, Set, Tuple
from collections import defaultdict, deque


def extraer_info_columna(raw_attr: Any) -> Tuple[str, str, bool]:
    """Retorna (nombre_columna, tipo_sql, es_fk)."""
    if isinstance(raw_attr, dict):
        nombre = str(raw_attr.get("nombre") or raw_attr.get("name") or "").strip().lstrip("+*-# ")
        tipo = str(raw_attr.get("tipo") or raw_attr.get("type") or "string").strip().lower()
        visibilidad = str(raw_attr.get("visibilidad") or "").upper()
        es_fk = visibilidad == "FK" or nombre.startswith("*") or nombre.lower().endswith("_id") or nombre.endswith("Id")
        return nombre, tipo, es_fk

    raw_str = str(raw_attr).strip()
    es_fk = raw_str.startswith("*") or "FK" in raw_str or "_id" in raw_str.lower() or "id" in raw_str.lower()
    clean = raw_str.lstrip("+*-# ")
    if ":" in clean:
        parts = clean.split(":", 1)
        name = parts[0].strip()
        dtype = parts[1].strip().lower()
    else:
        name = clean
        dtype = "string"
    return name, dtype, es_fk


def ordenar_topologicamente(
    nodes: List[Dict[str, Any]],
    relations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Ordena las entidades para que las tablas maestras se inserten antes que las dependientes."""
    table_by_name: Dict[str, Dict[str, Any]] = {}
    table_by_id: Dict[str, Dict[str, Any]] = {}

    for n in nodes:
        name = str(n.get("name") or n.get("nombre") or "").strip()
        n_id = str(n.get("id") or name).strip()
        if name:
            table_by_name[name] = n
            table_by_name[name.lower()] = n
            # Variaciones singular/plural para resolución de dependencias
            if name.lower().endswith("s"):
                table_by_name[name.lower()[:-1]] = n
            else:
                table_by_name[f"{name.lower()}s"] = n

            table_by_id[n_id] = n
            table_by_id[n_id.lower()] = n

    dependencias: Dict[str, Set[str]] = defaultdict(set)
    grados_entrada: Dict[str, int] = defaultdict(int)

    for n in nodes:
        t_name = str(n.get("name") or n.get("nombre") or "").strip()
        if t_name:
            grados_entrada[t_name] = 0

    # 1. Dependencias detectadas por nombres de columnas (FKs)
    for n in nodes:
        t_name = str(n.get("name") or n.get("nombre") or "").strip()
        if not t_name:
            continue
        attrs = n.get("attributes") or n.get("atributos") or []
        for a in attrs:
            col_name, _, es_fk = extraer_info_columna(a)
            c_low = col_name.lower().lstrip("*")
            if es_fk or c_low.endswith("_id") or c_low.endswith("id"):
                cand = re.sub(r"(_id|id)$", "", c_low)
                if cand in table_by_name:
                    parent_node = table_by_name[cand]
                    parent_name = str(parent_node.get("name") or parent_node.get("nombre"))
                    if parent_name != t_name:
                        dependencias[parent_name].add(t_name)

    # 2. Dependencias detectadas por relaciones del diagrama
    for r in relations:
        s_id = str(r.get("sourceId") or r.get("source") or "").strip()
        t_id = str(r.get("targetId") or r.get("target") or "").strip()
        s_node = table_by_id.get(s_id.lower())
        t_node = table_by_id.get(t_id.lower())
        r_type = str(r.get("type") or "").lower()

        if s_node and t_node and s_node != t_node:
            s_name = str(s_node.get("name") or s_node.get("nombre"))
            t_name = str(t_node.get("name") or t_node.get("nombre"))

            if r_type == "inheritance":
                # La subclase depende de la superclase
                dependencias[t_name].add(s_name)
            elif r_type in ["composition", "composition_to_part"]:
                # La parte depende del todo
                dependencias[s_name].add(t_name)
            elif r_type in ["1:n", "0..1:n"]:
                # La entidad hija (N) depende del padre (1)
                dependencias[s_name].add(t_name)
            elif r_type in ["association", "directed"]:
                # Dependencia tentativa origen -> destino
                dependencias[s_name].add(t_name)

    for parent, hijos in dependencias.items():
        for hijo in hijos:
            if hijo in grados_entrada:
                grados_entrada[hijo] += 1

    cola = deque([t for t, g in grados_entrada.items() if g == 0])
    orden: List[Dict[str, Any]] = []

    while cola:
        curr = cola.popleft()
        if curr in table_by_name:
            target_node = table_by_name[curr]
            if target_node not in orden:
                orden.append(target_node)
        for hijo in dependencias[curr]:
            grados_entrada[hijo] -= 1
            if grados_entrada[hijo] == 0:
                cola.append(hijo)

    # Añadir tablas pendientes en caso de grafos cíclicos o huérfanas
    agregadas = {str(n.get("name") or n.get("nombre")) for n in orden}
    for n in nodes:
        n_name = str(n.get("name") or n.get("nombre"))
        if n_name and n_name not in agregadas:
            orden.append(n)
            agregadas.add(n_name)

    return orden

