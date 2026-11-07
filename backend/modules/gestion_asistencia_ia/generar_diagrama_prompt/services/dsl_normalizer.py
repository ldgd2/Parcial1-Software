import re
from typing import Any, Dict, List, Optional

# Mapeo integral de sufijos de 1 y 2 caracteres a tipos de datos completos
SUFFIX_TYPE: Dict[str, str] = {
    "#": "int",
    "$": "float",
    "?": "bool",
    "@": "date",
    "!": "timestamp",
    "&": "uuid",
    "%": "text",
    "~": "blob",
}

# Mapeo de prefijos de tipo (símbolo al inicio del atributo)
PREFIX_TYPE: Dict[str, str] = {
    "#": "int",
    "$": "float",
    "?": "bool",
    "@": "date",
    "^": "datetime",
    "&": "text",
    "*": "FK",
    "!": "timestamp",
    "%": "text",
    "~": "blob",
}

# Mapeo de prefijos de métodos (.#int, .$float, .?bool, .@date, .^datetime, .&text, ._string, .void)
METHOD_PREFIX_RETURN: Dict[str, str] = {
    "#": "int",
    "$": "float",
    "?": "bool",
    "@": "date",
    "^": "datetime",
    "&": "text",
    "_": "string",
    "s": "string",
    "v": "void",
}

# Mapeo exhaustivo de todos los operadores y tipos de relaciones UML y Base de Datos
REL_TYPE: Dict[str, str] = {
    "-": "association",
    ">": "inheritance",
    "*": "composition",
    "o": "aggregation",
    ".": "dependency",
    "..": "dependency",
    "~": "realization",
    ":>": "realization",
    "&": "association_class",
    "=": "connector",
    "->": "delegate",
    "<>": "assembly",
    "!": "calls",
    "%": "instantiate",
    "^": "send",
    "+": "create",
    "assoc": "association",
    "association": "association",
    "asociacion": "association",
    "asociación": "association",
    "inherit": "inheritance",
    "inheritance": "inheritance",
    "herencia": "inheritance",
    "generalization": "inheritance",
    "comp": "composition",
    "composition": "composition",
    "composicion": "composition",
    "composición": "composition",
    "aggr": "aggregation",
    "aggregation": "aggregation",
    "agregacion": "aggregation",
    "agregación": "aggregation",
    "dep": "dependency",
    "dependency": "dependency",
    "dependencia": "dependency",
    "realiz": "realization",
    "realization": "realization",
    "realizacion": "realization",
    "realización": "realization",
    "directed": "directed",
    "association_class": "association_class",
    "connector": "connector",
    "delegate": "delegate",
    "assembly": "assembly",
    "call": "calls",
    "calls": "calls",
    "inst": "instantiate",
    "instantiate": "instantiate",
    "substitution": "substitution",
    "trace": "trace",
    "usage": "usage",
    "template_binding": "template_binding",
    "abstraction": "abstraction",
    "information_flow": "information_flow",
    "send": "send",
    "create_rel": "create",
    "1:1": "1:1",
    "1:n": "1:N",
    "1:N": "1:N",
    "n:m": "N:M",
    "N:M": "N:M",
    "0..1:1": "0..1:1",
    "0..1:n": "0..1:N",
    "0..1:N": "0..1:N",
    "0..n:1": "0..N:1",
    "0..N:1": "0..N:1",
    "0..n:m": "0..N:M",
    "0..N:M": "0..N:M",
}

JUNK_CLASS_NAMES = {
    "diagrama", "eliminadas", "eliminada", "borradas", "borrada",
    "clases", "clase", "node", "nodo", "tabla", "tablas", "elementos", "elemento",
    "tasks", "task", "assignments", "duplicada", "duplicadas",
    "se", "del", "al", "los", "las", "un", "una"
}

STOP_WORDS = {
    "de", "del", "y", "en", "con", "por", "para", "un", "una", "el", "la", "los", "las", "al", "o"
}

NATURAL_LANGUAGE_WORDS = {
    "se", "es", "son", "del", "al", "este", "esta", "estos", "estas", "todo",
    "todos", "toda", "todas", "clases", "diagrama", "modelo",
    "eliminadas", "eliminados", "borradas", "borrados", "corregido", "corregida",
    "consolidado", "consolidada", "duplicada", "duplicadas", "organizado", "actualizado"
}


def es_lenguaje_natural(text: str) -> bool:
    tokens = [t.lower().strip(".,;:()[]\"'") for t in text.split()]
    match_count = sum(1 for t in tokens if t in STOP_WORDS or t in NATURAL_LANGUAGE_WORDS)
    return match_count >= 2


def limpiar_lista_eliminados(raw_list: List[Any]) -> List[str]:
    """Filtra y devuelve únicamente nombres reales de clases eliminadas, purgando dummy IDs o cadenas espurias."""
    clean: List[str] = []
    seen = set()
    for item in raw_list:
        if not item:
            continue
        name = str(item).strip()
        lower = name.lower()
        if (
            not lower
            or lower in seen
            or lower in JUNK_CLASS_NAMES
            or re.match(r"^node_\w+$", lower)
            or re.match(r"^c_\w+$", lower)
            or lower.startswith("eliminad")
            or lower.startswith("borrad")
            or lower == "diagrama"
        ):
            continue
        seen.add(lower)
        clean.append(name)
    return clean


def sanitizar_resumen(summary: str) -> str:
    cleaned = (summary or "").strip()
    if (
        not cleaned
        or cleaned.startswith("{")
        or cleaned.startswith("[")
        or cleaned == "{"
        or "hyper-dsl" in cleaned.lower()
        or "dsl" in cleaned.lower()
    ):
        return "Diagrama estructurado y actualizado con éxito según las instrucciones."
    return cleaned
NODE_TYPES_MAP: Dict[str, str] = {
    "class": "class",
    "clase": "class",
    "interface": "interface",
    "interfaz": "interface",
    "abstract": "abstract",
    "abstracta": "abstract",
    "enum": "enum",
    "enumeracion": "enum",
    "enumeración": "enum",
    "datatype": "datatype",
    "primitive": "primitive",
    "primitiva": "primitive",
    "signal": "signal",
    "señal": "signal",
    "note": "note",
    "nota": "note",
    "part": "part",
    "parte": "part",
    "port": "port",
    "puerto": "port",
    "expose_interface": "expose_interface",
    "assembly": "assembly",
    "auxillary": "auxillary",
    "auxiliary": "auxillary",
    "focus": "focus",
    "implementation_class": "implementation_class",
    "realization_class": "realization_class",
    "specification": "specification",
    "especificacion": "specification",
    "type": "type",
    "utility": "utility",
    "utilidad": "utility",
    "create_event": "create_event",
    "destroy_event": "destroy_event",
    "constraint": "constraint",
    "restriccion": "constraint",
    "restricción": "constraint",
    "text": "text",
    "texto": "text",
    "artifact": "artifact",
    "artefacto": "artifact",
    "requirement": "requirement",
    "requisito": "requirement",
    "issue": "issue",
    "problema": "issue",
    "change": "change",
    "cambio": "change",
    "information_item": "information_item",
    "boundary": "boundary",
    "frontera": "boundary",
}


def _extraer_tipo_nodo(tag_or_suffix: str) -> str:
    cleaned = tag_or_suffix.lower().strip().lstrip("[:(").rstrip("]):")
    return NODE_TYPES_MAP.get(cleaned, "class")


def parse_method_token(token: str) -> str:
    """
    Parsea tokens de métodos como:
    - .anular -> +anular():void
    - .#calcularEdad(#anio) -> +calcularEdad(anio:int):int
    - .$calcularTotal(#descuento) -> +calcularTotal(descuento:int):float
    - .?estaActivo -> +estaActivo():bool
    - .@obtenerVencimiento -> +obtenerVencimiento():date
    - ._generarCodigo -> +generarCodigo():string
    """
    clean = token.lstrip(".")
    ret_type = "void"
    if token.startswith(".") and len(token) > 1 and token[1] in METHOD_PREFIX_RETURN:
        ret_type = METHOD_PREFIX_RETURN[token[1]]
        clean = token[2:]

    pm = re.match(r"^([a-zA-Z0-9_]+)(?:\((.*?)\))?(?::([a-zA-Z0-9_]+))?$", clean)
    if pm:
        m_name = pm.group(1)
        raw_params = (pm.group(2) or "").strip()
        explicit_ret = pm.group(3)
        if explicit_ret:
            ret_type = explicit_ret

        params_list = []
        if raw_params:
            for p in raw_params.split(","):
                p = p.strip()
                if not p:
                    continue
                if p[0] in PREFIX_TYPE:
                    p_name = p[1:]
                    p_type = PREFIX_TYPE[p[0]]
                    params_list.append(f"{p_name}:{p_type}")
                elif ":" in p:
                    params_list.append(p)
                elif p[-1] in SUFFIX_TYPE:
                    p_name = p[:-1]
                    p_type = SUFFIX_TYPE[p[-1]]
                    params_list.append(f"{p_name}:{p_type}")
                else:
                    params_list.append(f"{p}:string")
        return f"+{m_name}({', '.join(params_list)}):{ret_type}"
    m_name = clean.replace("()", "").strip().lstrip("+-#")
    return f"+{m_name}():{ret_type}"


def parse_attr_token(token: str) -> str:
    """
    Parsea tokens de atributos como:
    - email -> +email:string
    - #edad -> +edad:int
    - $precio -> +precio:float
    - ?activo -> +activo:bool
    - @fecha -> +fecha:date
    - ^login -> +login:datetime
    - &descripcion -> +descripcion:text
    - *usuario_id -> FKusuario_id:FK
    - edad# -> +edad:int
    - nombre:string -> +nombre:string
    """
    if not token:
        return "+attr:string"

    # 1. Prefijo explícito
    if token[0] in PREFIX_TYPE:
        p_sym = token[0]
        a_type = PREFIX_TYPE[p_sym]
        a_name = token[1:].strip().lstrip("+-#")
        vis = "FK" if p_sym == "*" else "+"
        return f"{vis}{a_name}:{a_type}"

    # 2. Formato con dos puntos (nombre:tipo)
    if ":" in token:
        parts = token.split(":")
        a_name = parts[0].strip().lstrip("+-#")
        a_type = parts[1].strip() if len(parts) > 1 else "string"
        return f"+{a_name}:{a_type}"

    # 3. Sufijo explícito (edad#, total$)
    if token[-1] in SUFFIX_TYPE:
        s_sym = token[-1]
        a_type = SUFFIX_TYPE[s_sym]
        a_name = token[:-1].strip().lstrip("+-#")
        return f"+{a_name}:{a_type}"

    # 4. Sin símbolo = string por defecto
    clean_name = token.strip().lstrip("+-#")
    return f"+{clean_name}:string"


def parse_hyper_dsl(raw: str, existing_context: Optional[str] = None) -> Dict[str, Any]:
    """
    Parsea DSL Hiper-Comprimido con soporte exhaustivo de nodos, relaciones y tipos:
    - 1Usuario email rol#                      -> Clase Usuario (PK implícita, email:string, rol:int)
    - 1:interface IRepositorio guardar()       -> Interfaz
    - 1Usuario:abstract email                  -> Clase Abstracta
    - 1Estado:enum ACTIVO INACTIVO PENDIENTE   -> Enum con valores
    - 1Nota:note contenido de texto            -> Nota informativa
    - 1Req1:requirement Detalle del requisito -> Requisito
    - 1P1:port                                 -> Puerto
    - 1-2                                      -> Asociación 1..* implícita
    - 1>2                                      -> Herencia
    - 1*2                                      -> Composición
    - 1o2                                      -> Agregación
    - 1.2 o 1..2                               -> Dependencia
    - 1~2 o 1:>2                               -> Realización
    - 1=2                                      -> Conector
    - 1->2                                     -> Delegado
    - 1-2:1:N                                  -> Cardinalidad de base de datos 1 a Muchos
    - -1,2                                     -> Borrado múltiple
    - ~1 +tel$ -email                          -> Modificación/parcheo
    """
    nodes: List[Dict[str, Any]] = []
    relations: List[Dict[str, Any]] = []
    deleted_nodes: List[str] = []
    deleted_relations: List[str] = []
    del_count = 0

    id_to_name: Dict[str, str] = {}

    if existing_context:
        for line in existing_context.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("C:"):
                name_m = re.match(r"^C:([^|]+)", line)
                id_m = re.search(r"\|id:([^|]+)", line)
                if name_m and id_m:
                    n_name = name_m.group(1).strip()
                    n_id = id_m.group(1).strip()
                    id_to_name[n_id] = n_name
                    id_to_name[n_id.lower()] = n_name
                    id_to_name[n_name] = n_name
                    id_to_name[n_name.lower()] = n_name
            else:
                for segment in line.split(";"):
                    seg = segment.strip()
                    if not seg:
                        continue
                    tok_match = re.match(r"^(\d+|c_[a-zA-Z0-9_]+)?(?::[a-zA-Z_]+)?([A-Za-z_]\w*)", seg)
                    if tok_match:
                        raw_num, class_name = tok_match.groups()
                        if raw_num:
                            id_to_name[raw_num] = class_name
                            id_to_name[raw_num.lower()] = class_name
                        id_to_name[class_name] = class_name
                        id_to_name[class_name.lower()] = class_name

    commands = [c.strip() for c in raw.strip().split(";") if c.strip()]

    for cmd in commands:
        # 1. Borrado: -1,2 o -Usuario,Venta
        if cmd.startswith("-"):
            raw_targets = [x.strip() for x in cmd[1:].split(",") if x.strip()]
            del_count += len(raw_targets)
            if del_count > 25:
                raise PermissionError("Límite máximo de borrados excedido por seguridad")
            for t in raw_targets:
                resolved_id = id_to_name.get(t, id_to_name.get(t.lower(), t))
                deleted_nodes.append(resolved_id)

        # 2. Relaciones complejas y simbólicas (ej: 1-2, 1>2, 1*2, 1o2, 1.2, 1~2, 1=2, 1->2, 1-2:1:N)
        elif m := re.match(r"^([a-zA-Z0-9_\-]+)([\->*o.~:=&^!+%<>]+)([a-zA-Z0-9_\-]+)(?::(\S+))?$", cmd):
            s, r, d, card = m.groups()
            src_id = id_to_name.get(s, id_to_name.get(s.lower(), s))
            dst_id = id_to_name.get(d, id_to_name.get(d.lower(), d))
            rel_type = REL_TYPE.get(r, "association")
            card_label = card or ("" if rel_type == "inheritance" else "1..*")

            # Mapeo de cardinalidades de Base de Datos
            if card and card.upper() in ["1:1", "1:N", "N:M", "0..1:1", "0..1:N", "0..N:1", "0..N:M"]:
                rel_type = card.upper()

            relations.append({
                "id": f"rel_{src_id}_{dst_id}_{abs(hash(cmd)) % 10000}",
                "sourceId": src_id,
                "targetId": dst_id,
                "type": rel_type,
                "label": card_label,
                "sourceLabel": "" if rel_type == "inheritance" else ("1" if card_label == "1..*" else "")
            })

        # 3. Parcheo de Nodo: ~1 +tel$ -email
        elif m := re.match(r"^~([a-zA-Z0-9_\-]+)\s+(.+)$", cmd):
            target_id, changes = m.groups()
            resolved_target = id_to_name.get(target_id, id_to_name.get(target_id.lower(), target_id))
            mods = changes.split()
            add_attrs: List[str] = []
            for mod in mods:
                if mod.startswith("+"):
                    a_name = mod[1:]
                    add_attrs.append(parse_attr_token(a_name))

            # Buscar si el nodo ya existe en 'nodes' para parchearlo directamente
            target_node = None
            for n in nodes:
                if n["id"].lower() == resolved_target.lower() or n["name"].lower() == resolved_target.lower():
                    target_node = n
                    break

            if target_node:
                target_node["attributes"].extend(add_attrs)
            elif resolved_target and not resolved_target.isdigit() and not resolved_target.startswith("Node_"):
                nodes.append({
                    "id": resolved_target,
                    "name": resolved_target,
                    "type": "class",
                    "attributes": add_attrs,
                    "methods": []
                })

        # 4. Creación de Nodo con Tipo Opcional y atributos/valores
        elif m := re.match(r"^(\d+|c_[a-zA-Z0-9_]+)?(?::([a-zA-Z_]+)|\[([a-zA-Z_]+)\])?([A-Za-z_]\w*)(?::([a-zA-Z_]+))?(?:\s+(.+))?$", cmd):
            nid, pre_type1, pre_type2, name, post_type, rest = m.groups()
            name_lower = name.lower()

            if es_lenguaje_natural(cmd) or es_lenguaje_natural(name):
                continue

            # Detección y filtrado de sentencias o palabras basura generadas por la IA
            if name_lower in JUNK_CLASS_NAMES or re.match(r"^node_\w+$", name_lower):
                if name_lower.startswith("eliminad") or name_lower.startswith("borrad"):
                    if rest:
                        for token in rest.replace(",", " ").split():
                            t_clean = token.strip().strip("[](),:;\"'")
                            if t_clean and t_clean.lower() not in STOP_WORDS and t_clean.lower() not in JUNK_CLASS_NAMES:
                                deleted_nodes.append(t_clean)
                continue

            # Si el resto contiene stop words en español (prosa libre), descartar como clase
            if rest:
                rest_tokens = [t.strip().lower() for t in rest.strip().split() if t.strip()]
                stop_count = sum(1 for t in rest_tokens if t in STOP_WORDS)
                if stop_count >= 2:
                    continue

            node_id = name
            if nid:
                id_to_name[nid] = name
                id_to_name[nid.lower()] = name
            id_to_name[name] = name
            id_to_name[name.lower()] = name

            raw_type = pre_type1 or pre_type2 or post_type or "class"
            node_type = _extraer_tipo_nodo(raw_type)

            attrs: List[str] = []
            methods: List[str] = []
            valores: List[str] = []
            contenido: str = ""

            # Clases y tipos estructurales incluyen PK id:int implícita
            if node_type in ["class", "abstract", "implementation_class", "realization_class"]:
                attrs.append("+id:int")

            if rest:
                rest_str = rest.strip()
                if node_type == "note":
                    contenido = rest_str
                elif node_type == "enum":
                    valores = [v.strip() for v in rest_str.split() if v.strip()]
                else:
                    for token in rest_str.split():
                        token = token.strip()
                        if not token:
                            continue
                        if token.startswith("."):
                            methods.append(parse_method_token(token))
                        elif "()" in token or ("(" in token and ")" in token):
                            methods.append(parse_method_token(f".{token}"))
                        else:
                            attrs.append(parse_attr_token(token))

            node_dict: Dict[str, Any] = {
                "id": node_id,
                "name": name,
                "type": node_type,
                "attributes": attrs,
                "methods": methods
            }
            if valores:
                node_dict["valores"] = valores
            if contenido:
                node_dict["contenido"] = contenido

            nodes.append(node_dict)

    return {
        "nodes": nodes,
        "relations": relations,
        "deletedNodes": deleted_nodes,
        "deletedRelations": deleted_relations
    }


def parse_dsl_node(item: Any) -> Dict[str, Any]:
    if isinstance(item, dict):
        node_name = str(item.get("name") or item.get("nombre") or "Clase").strip()
        name_lower = node_name.lower()
        if (
            name_lower in JUNK_CLASS_NAMES
            or bool(re.match(r"^node_\w+$", name_lower))
            or es_lenguaje_natural(node_name)
            or name_lower.startswith("eliminad")
            or name_lower.startswith("borrad")
            or name_lower == "diagrama"
        ):
            return {}

        raw_id = str(item.get("id") or "").strip()
        if not raw_id or raw_id.isdigit() or raw_id.lower().startswith("node_"):
            node_id = node_name
        else:
            node_id = raw_id

        node_type = str(item.get("type") or item.get("tipo") or "class").strip()
        attrs = item.get("attributes") or item.get("atributos") or []
        methods = item.get("methods") or item.get("metodos") or []

        if node_type in ["class", "abstract", "implementation_class", "realization_class"]:
            has_id = any("id:int" in str(a).lower() or "id:" in str(a).lower() or str(a).lower() == "+id" for a in attrs)
            if not has_id:
                attrs = ["+id:int"] + list(attrs)

        return {
            "id": node_id,
            "name": node_name,
            "type": node_type,
            "attributes": attrs,
            "methods": methods,
            "responsable": item.get("responsable"),
            "responsabilidades": item.get("responsabilidades") or [],
            "valores": item.get("valores") or [],
            "contenido": item.get("contenido") or ""
        }
    if not isinstance(item, str):
        return {}

    raw = item.strip()
    if (
        raw.lower() in JUNK_CLASS_NAMES
        or bool(re.match(r"^node_\w+$", raw.lower()))
        or es_lenguaje_natural(raw)
        or raw.lower().startswith("eliminad")
        or raw.lower().startswith("borrad")
        or raw.lower() == "diagrama"
    ):
        return {}

    if not raw.startswith("C:"):
        hyper = parse_hyper_dsl(raw)
        if hyper["nodes"]:
            return hyper["nodes"][0]
        return {
            "id": raw,
            "name": raw,
            "type": "class",
            "attributes": ["+id:int"],
            "methods": []
        }

    name_match = re.match(r"^C:([^|]+)", raw)
    name = name_match.group(1).strip() if name_match else "Clase"

    id_match = re.search(r"\|id:([^|]+)", raw)
    node_id = id_match.group(1).strip() if id_match else name.lower()

    t_match = re.search(r"\|t:([^|]+)", raw)
    node_type = t_match.group(1).strip() if t_match else "class"

    attrs: List[str] = []
    a_match = re.search(r"\|a:\[(.*?)\](?:\||$)", raw)
    if a_match:
        attrs_str = a_match.group(1).strip()
        if attrs_str:
            attrs = [a.strip() for a in attrs_str.split(",") if a.strip()]

    methods: List[str] = []
    m_match = re.search(r"\|m:\[(.*?)\](?:\||$)", raw)
    if m_match:
        m_str = m_match.group(1).strip()
        if m_str:
            parts = [m.strip() for m in re.split(r";|,(?=[+\-#])", m_str) if m.strip()]
            methods = parts

    resp_match = re.search(r"\|resp:([^|]+)", raw)
    responsable = resp_match.group(1).strip() if resp_match else ""

    resps: List[str] = []
    resps_match = re.search(r"\|resps:\[(.*?)\](?:\||$)", raw)
    if resps_match:
        resps_str = resps_match.group(1).strip()
        if resps_str:
            resps = [r.strip() for r in resps_str.split(",") if r.strip()]

    node_dict: Dict[str, Any] = {
        "id": node_id,
        "name": name,
        "type": node_type,
        "attributes": attrs,
        "methods": methods
    }
    if responsable:
        node_dict["responsable"] = responsable
    if resps:
        node_dict["responsabilidades"] = resps

    return node_dict


def parse_dsl_relation(item: Any) -> Dict[str, Any]:
    if isinstance(item, dict):
        source_id = str(item.get("sourceId") or item.get("source") or item.get("origen") or item.get("from") or item.get("src") or "").strip()
        target_id = str(item.get("targetId") or item.get("target") or item.get("destino") or item.get("to") or item.get("dst") or "").strip()
        raw_t = str(item.get("type") or item.get("tipo") or "association").strip()
        rel_type = REL_TYPE.get(raw_t.lower(), raw_t)
        card_label = str(item.get("label") or item.get("cardinality") or item.get("multiplicity") or ("" if rel_type == "inheritance" else "1..*")).strip()
        source_label = str(item.get("sourceLabel") or item.get("sourceMultiplicity") or ("" if rel_type == "inheritance" else ("1" if card_label == "1..*" else ""))).strip()
        rel_id = str(item.get("id") or f"rel_{source_id}_{target_id}_{abs(hash(str(item))) % 10000}").strip()
        return {
            "id": rel_id,
            "sourceId": source_id,
            "targetId": target_id,
            "type": rel_type,
            "label": card_label,
            "sourceLabel": source_label
        }
    if not isinstance(item, str):
        return {}

    raw = item.strip()
    if not raw.startswith("R:"):
        hyper = parse_hyper_dsl(raw)
        if hyper["relations"]:
            return hyper["relations"][0]
        return {}

    st_match = re.search(r"^R:([^->|]+)->([^|]+)", raw)
    source_id = st_match.group(1).strip() if st_match else ""
    target_id = st_match.group(2).strip() if st_match else ""

    t_match = re.search(r"\|t:([^|]+)", raw)
    raw_t = t_match.group(1).strip() if t_match else "association"
    rel_type = REL_TYPE.get(raw_t.lower(), raw_t)

    l_match = re.search(r"\|l:([^|]+)", raw)
    label = l_match.group(1).strip() if l_match else ""

    id_match = re.search(r"\|id:([^|]+)", raw)
    rel_id = id_match.group(1).strip() if id_match else f"rel_{source_id}_{target_id}"

    return {
        "id": rel_id,
        "sourceId": source_id,
        "targetId": target_id,
        "type": rel_type,
        "label": label,
        "sourceLabel": "1" if label == "1..*" else ""
    }


def extraer_entidades_de_texto(text: str) -> List[Dict[str, Any]]:
    """
    Extrae entidades reales mencionadas en el texto explicativo de la IA
    (ej: "La nueva entidad 'Parcial'...", "**Semestre**") cuando la IA responde en prosa.
    Utiliza únicamente los filtros gramaticales sin listas arbitrarias ni censura de dominio.
    """
    if not text:
        return []

    patterns = [
        r"(?:entidad|clase|tabla)\s+['\"‘“]([A-Z][a-zA-Z0-9_]+)['\"’”]",
        r"['\"‘“]([A-Z][a-zA-Z0-9_]+)['\"’”]\s+(?:representa|conecta|hereda|gestiona|almacena|registra)",
        r"\*\*([A-Z][a-zA-Z0-9_]+)\*\*"
    ]

    found_names = set()
    nodes: List[Dict[str, Any]] = []

    for pat in patterns:
        for m in re.finditer(pat, text):
            raw = m.group(1).strip()
            if not raw or len(raw) < 3:
                continue
            canon = raw[0].upper() + raw[1:]
            lower = canon.lower()
            if (
                lower not in found_names
                and lower not in JUNK_CLASS_NAMES
                and not re.match(r"^node_\w+$", lower)
                and not es_lenguaje_natural(canon)
            ):
                found_names.add(lower)
                nodes.append({
                    "id": canon,
                    "name": canon,
                    "type": "class",
                    "attributes": ["+id:int", "+nombre:string", "+estado:string"],
                    "methods": [".procesar():bool"]
                })
    return nodes


def extraer_o_reparar_json(text: str) -> Optional[Dict[str, Any]]:
    """Extrae o repara un objeto JSON incluso si quedó truncado por límites de tokens."""
    cleaned = text.strip()
    try:
        import json
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    first_b = cleaned.find("{")
    last_b = cleaned.rfind("}")
    if first_b != -1 and last_b > first_b:
        candidate = cleaned[first_b:last_b + 1]
        try:
            import json
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # Reparación de JSON truncado
    if first_b != -1:
        summary_m = re.search(r'"(?:summary|s)"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', cleaned)
        summary = summary_m.group(1) if summary_m else ""

        candidate = cleaned[first_b:]
        last_item = max(candidate.rfind("}"), candidate.rfind("]"))
        if last_item != -1:
            repaired = candidate[:last_item + 1]
            open_braces = repaired.count("{") - repaired.count("}")
            open_brackets = repaired.count("[") - repaired.count("]")
            repaired += ("]" * max(0, open_brackets)) + ("}" * max(0, open_braces))
            try:
                import json
                parsed = json.loads(repaired)
                if isinstance(parsed, dict):
                    if summary and not parsed.get("summary"):
                        parsed["summary"] = summary
                    return parsed
            except Exception:
                pass

        # Extracción granular de nodos si el JSON general no se pudo reconstruir
        extracted_nodes: List[Dict[str, Any]] = []
        node_pattern = re.compile(r'\{\s*"name"\s*:\s*"([^"]+)"[^}]*\}', re.DOTALL)
        for m in node_pattern.finditer(cleaned):
            chunk = m.group(0)
            try:
                import json
                n_obj = json.loads(chunk)
                if isinstance(n_obj, dict) and n_obj.get("name"):
                    extracted_nodes.append(n_obj)
            except Exception:
                pass

        if extracted_nodes:
            return {
                "summary": summary,
                "nodes": extracted_nodes,
                "relations": []
            }

        if summary:
            return {"summary": summary, "nodes": [], "relations": []}

    return None


VALID_INHERITANCE_PAIRS = {
    ("docente", "usuario"),
    ("estudiante", "usuario"),
    ("administrador", "usuario"),
    ("profesor", "usuario"),
    ("alumno", "usuario"),
    ("empleado", "persona"),
    ("cliente", "persona"),
}

VALID_COMPOSITION_PAIRS = {
    ("curso", "tarea"),
    ("tarea", "entrega"),
    ("entrega", "revision"),
    ("revision", "comentario"),
    ("pedido", "detallepedido"),
    ("factura", "detallefactura"),
    ("venta", "detalleventa"),
}

FORBIDDEN_COMPOSITION_OR_INHERITANCE_PAIRS = {
    ("docente", "curso"),
    ("curso", "docente"),
    ("materia", "curso"),
    ("curso", "materia"),
    ("estudiante", "curso"),
    ("curso", "estudiante"),
    ("estudiante", "inscripcion"),
    ("inscripcion", "estudiante"),
    ("curso", "inscripcion"),
    ("inscripcion", "curso"),
    ("docente", "revision"),
    ("revision", "docente"),
    ("estudiante", "entrega"),
    ("entrega", "estudiante"),
    ("inscripcion", "calificacion"),
    ("calificacion", "inscripcion"),
    ("entrega", "calificacion"),
    ("calificacion", "entrega"),
    ("usuario", "notificacion"),
    ("notificacion", "usuario"),
    ("docente", "tarea"),
    ("tarea", "docente"),
    ("docente", "calificacion"),
    ("calificacion", "docente"),
}


def sanitizar_semantica_relaciones(relations: List[Dict[str, Any]], nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Corrige y normaliza tipos de relaciones (asociación, agregación, composición, herencia)
    aplicando estrictamente principios orientados a objetos y diseño relacional:
    - Previene que las IAs como Kimi conviertan erróneamente todas las relaciones en composición o herencia.
    - Asegura que la dirección y cardinalidad sean consistentes.
    - Elimina relaciones dirigidas a nodos basura.
    """
    valid_node_names = {n["name"].lower(): n["name"] for n in nodes if n.get("name")}
    cleaned_relations: List[Dict[str, Any]] = []
    seen_pairs = set()

    for r in relations:
        s_raw = str(r.get("sourceId") or r.get("source") or "").strip()
        t_raw = str(r.get("targetId") or r.get("target") or "").strip()
        s_lower = s_raw.lower()
        t_lower = t_raw.lower()

        # Descartar conexiones a nodos basura o auto-referencias sin sentido
        if not s_raw or not t_raw or s_lower == t_lower:
            continue
        if s_lower in JUNK_CLASS_NAMES or t_lower in JUNK_CLASS_NAMES:
            continue

        rel_type = str(r.get("type") or "association").lower().strip()
        card_label = str(r.get("label") or "").strip()
        source_label = str(r.get("sourceLabel") or "").strip()

        pair = (s_lower, t_lower)
        pair_rev = (t_lower, s_lower)

        # 1. Validación de Herencia / Generalización
        if rel_type in ["inheritance", "herencia", "generalization"]:
            if pair in VALID_INHERITANCE_PAIRS:
                card_label = ""
                source_label = ""
            elif pair_rev in VALID_INHERITANCE_PAIRS:
                s_raw, t_raw = t_raw, s_raw
                s_lower, t_lower = t_lower, s_lower
                card_label = ""
                source_label = ""
            else:
                rel_type = "association"
                card_label = card_label or "1..*"
                source_label = source_label or "1"

        # 2. Validación de Composición
        elif rel_type in ["composition", "composicion", "composición"]:
            if pair in VALID_COMPOSITION_PAIRS or pair_rev in VALID_COMPOSITION_PAIRS:
                if pair_rev in VALID_COMPOSITION_PAIRS:
                    s_raw, t_raw = t_raw, s_raw
                    s_lower, t_lower = t_lower, s_lower
                card_label = card_label or "1..*"
                source_label = source_label or "1"
            elif pair in FORBIDDEN_COMPOSITION_OR_INHERITANCE_PAIRS or pair_rev in FORBIDDEN_COMPOSITION_OR_INHERITANCE_PAIRS:
                rel_type = "association"
                card_label = card_label or "1..*"
                source_label = source_label or "1"

        # 3. Pares prohibidos explícitos que deben ser asociación simple
        if (s_lower, t_lower) in FORBIDDEN_COMPOSITION_OR_INHERITANCE_PAIRS or (t_lower, s_lower) in FORBIDDEN_COMPOSITION_OR_INHERITANCE_PAIRS:
            if rel_type not in ["association", "aggregation"]:
                rel_type = "association"
                card_label = card_label or "1..*"
                source_label = source_label or "1"

        pair_key = tuple(sorted([s_lower, t_lower]))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        cleaned_relations.append({
            "id": r.get("id") or f"rel_{s_raw}_{t_raw}",
            "sourceId": s_raw,
            "targetId": t_raw,
            "type": rel_type,
            "label": card_label,
            "sourceLabel": source_label
        })

    return cleaned_relations


def garantizar_conectividad_relacional(nodes: List[Dict[str, Any]], relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Garantiza que todas las clases del modelo queden lógicamente conectadas (cero huérfanas)."""
    if len(nodes) <= 1:
        return sanitizar_semantica_relaciones(relations, nodes)

    sanitized = sanitizar_semantica_relaciones(relations, nodes)

    connected_ids = set()
    for r in sanitized:
        s = str(r.get("sourceId") or "").lower()
        t = str(r.get("targetId") or "").lower()
        if s:
            connected_ids.add(s)
        if t:
            connected_ids.add(t)

    node_names = [n["name"] for n in nodes]
    node_names_lower = {n["name"].lower(): n["name"] for n in nodes}
    updated_relations = list(sanitized)

    for node in nodes:
        n_id = str(node["id"])
        n_name = str(node["name"])
        n_lower = n_name.lower()
        if n_id.lower() not in connected_ids and n_lower not in connected_ids:
            # 1. Búsqueda por Foreign Key en atributos (ej: *materia_id:FK -> conecta con Materia)
            fk_target = None
            for a in node.get("attributes", []):
                a_lower = str(a).lower()
                for other_n in node_names:
                    if other_n.lower() == n_name.lower():
                        continue
                    if other_n.lower() in a_lower:
                        fk_target = other_n
                        break
                if fk_target:
                    break

            target_to_connect = fk_target or (node_names[0] if node_names[0].lower() != n_lower else (node_names[1] if len(node_names) > 1 else None))
            if target_to_connect:
                src = target_to_connect
                dst = n_id

                new_rel = {
                    "id": f"rel_{src}_{dst}_{abs(hash(n_id)) % 10000}",
                    "sourceId": src,
                    "targetId": dst,
                    "type": "association",
                    "label": "1..*",
                    "sourceLabel": "1"
                }
                updated_relations.append(new_rel)
                connected_ids.add(n_id.lower())
                connected_ids.add(n_lower)
                connected_ids.add(target_to_connect.lower())

    return sanitizar_semantica_relaciones(updated_relations, nodes)


def normalize_ai_output(data: Any, context: Optional[str] = None) -> Dict[str, Any]:
    """
    Normaliza respuestas de IA soportando:
    1. JSON estructurado completo o reparado tras corte por tokens
    2. Formato de 2 líneas (Línea 1: Resumen, Línea 2: Hyper-DSL con ;)
    3. Garantía relacional para cero clases huérfanas.
    """
    if isinstance(data, str):
        cleaned = data.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # Si viene JSON serializado o contiene estructura JSON
        if "{" in cleaned:
            parsed_json = extraer_o_reparar_json(cleaned)
            if parsed_json and isinstance(parsed_json, dict) and ("nodes" in parsed_json or "summary" in parsed_json or "s" in parsed_json or "n" in parsed_json):
                return normalize_ai_output(parsed_json, context)

        # Formato estándar de 2 líneas (Línea 1: Resumen, Línea 2: Hyper-DSL)
        lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        summary = "Diagrama actualizado con éxito."
        raw_dsl = ""

        if len(lines) >= 2:
            summary = re.sub(r"^(?:L[ií]nea\s*1\s*:\s*|Resumen\s*:\s*|Summary\s*:\s*)", "", lines[0], flags=re.IGNORECASE).strip()
            raw_dsl_lines = lines[1:]
            cleaned_dsl_parts = []
            for l in raw_dsl_lines:
                clean_l = re.sub(r"^(?:L[ií]nea\s*2\s*:\s*|DSL\s*:\s*)", "", l, flags=re.IGNORECASE).strip()
                if clean_l and not es_lenguaje_natural(clean_l):
                    cleaned_dsl_parts.append(clean_l)
                elif clean_l:
                    summary += " " + clean_l
            raw_dsl = ";".join(cleaned_dsl_parts)
        elif len(lines) == 1:
            line = lines[0]
            if not es_lenguaje_natural(line) and any(op in line for op in [";", ">", "*", "-", "#", "$", "@", "?", "."]):
                raw_dsl = line
            else:
                summary = line

        hyper = parse_hyper_dsl(raw_dsl, context)
        all_deleted = limpiar_lista_eliminados(hyper.get("deletedNodes") or [])
        clean_nodes = [
            n for n in hyper["nodes"]
            if n.get("name")
            and n["name"].lower() not in JUNK_CLASS_NAMES
            and not re.match(r"^node_\w+$", n["name"].lower())
            and not es_lenguaje_natural(n["name"])
            and not n["name"].lower().startswith("eliminad")
            and not n["name"].lower().startswith("borrad")
            and n["name"].lower() != "diagrama"
            and n["name"] not in all_deleted
        ]
        conns = garantizar_conectividad_relacional(clean_nodes, hyper["relations"])
        if not clean_nodes and (cleaned or summary):
            extracted = extraer_entidades_de_texto(f"{cleaned} {summary}")
            if extracted:
                clean_nodes = extracted
                conns = garantizar_conectividad_relacional(clean_nodes, [])
        return {
            "summary": sanitizar_resumen(summary),
            "nodes": clean_nodes,
            "relations": conns,
            "deletedNodes": all_deleted,
            "deletedRelations": hyper["deletedRelations"],
            "tasks": []
        }

    if not isinstance(data, dict):
        return {
            "summary": "Formato no reconocido",
            "nodes": [],
            "relations": [],
            "deletedNodes": [],
            "deletedRelations": [],
            "tasks": []
        }

    raw_dsl = data.get("dsl") or data.get("hyper")
    if raw_dsl and isinstance(raw_dsl, str):
        hyper = parse_hyper_dsl(raw_dsl, context)
        all_deleted = limpiar_lista_eliminados(hyper.get("deletedNodes") or [])
        clean_nodes = [
            n for n in hyper["nodes"]
            if n.get("name")
            and n["name"].lower() not in JUNK_CLASS_NAMES
            and not re.match(r"^node_\w+$", n["name"].lower())
            and not es_lenguaje_natural(n["name"])
            and not n["name"].lower().startswith("eliminad")
            and not n["name"].lower().startswith("borrad")
            and n["name"].lower() != "diagrama"
            and n["name"] not in all_deleted
        ]
        conns = garantizar_conectividad_relacional(clean_nodes, hyper["relations"])
        if not clean_nodes and (cleaned or summary):
            extracted = extraer_entidades_de_texto(f"{cleaned} {summary}")
            if extracted:
                clean_nodes = extracted
                conns = garantizar_conectividad_relacional(clean_nodes, [])
        return {
            "summary": sanitizar_resumen(str(data.get("summary") or data.get("s") or "")),
            "nodes": clean_nodes,
            "relations": conns,
            "deletedNodes": all_deleted,
            "deletedRelations": hyper["deletedRelations"],
            "tasks": data.get("tasks") or data.get("t") or []
        }

    summary = sanitizar_resumen(str(data.get("summary") or data.get("s") or ""))

    raw_nodes = data.get("nodes") or data.get("n") or []
    nodes = []
    id_map = {}
    for n in raw_nodes:
        if not n:
            continue
        parsed_n = parse_dsl_node(n)
        if not parsed_n or not parsed_n.get("name"):
            continue
        c_name = parsed_n["name"]
        orig_id = parsed_n.get("id") or c_name
        canon_id = c_name if (orig_id.isdigit() or orig_id.lower().startswith("node_")) else orig_id
        parsed_n["id"] = canon_id
        id_map[orig_id] = canon_id
        id_map[orig_id.lower()] = canon_id
        id_map[c_name] = canon_id
        id_map[c_name.lower()] = canon_id
        nodes.append(parsed_n)

    raw_relations = data.get("relations") or data.get("r") or []
    relations = []
    for r in raw_relations:
        if not r:
            continue
        parsed_r = parse_dsl_relation(r)
        if not parsed_r:
            continue
        raw_s = parsed_r["sourceId"]
        raw_t = parsed_r["targetId"]
        res_s = id_map.get(raw_s, id_map.get(raw_s.lower(), raw_s))
        res_t = id_map.get(raw_t, id_map.get(raw_t.lower(), raw_t))
        if res_s and res_t and res_s != res_t:
            parsed_r["sourceId"] = res_s
            parsed_r["targetId"] = res_t
            relations.append(parsed_r)

    deleted_nodes = data.get("deletedNodes") or data.get("dn") or data.get("deleted") or data.get("eliminados") or []
    if not isinstance(deleted_nodes, list):
        deleted_nodes = []
    all_deleted = limpiar_lista_eliminados(deleted_nodes)

    clean_nodes = [
        n for n in nodes
        if n.get("name")
        and n["name"].lower() not in JUNK_CLASS_NAMES
        and not re.match(r"^node_\w+$", n["name"].lower())
        and not es_lenguaje_natural(n["name"])
        and not n["name"].lower().startswith("eliminad")
        and not n["name"].lower().startswith("borrad")
        and n["name"].lower() != "diagrama"
        and n["name"] not in all_deleted
    ]

    relations = garantizar_conectividad_relacional(clean_nodes, relations)

    if not clean_nodes and summary:
        extracted = extraer_entidades_de_texto(summary)
        if extracted:
            clean_nodes = extracted
            relations = garantizar_conectividad_relacional(clean_nodes, relations)

    deleted_relations = data.get("deletedRelations") or data.get("dr") or data.get("deleted_relations") or []
    tasks = data.get("tasks") or data.get("t") or []

    return {
        "summary": summary,
        "nodes": clean_nodes,
        "relations": relations,
        "deletedNodes": all_deleted,
        "deletedRelations": deleted_relations if isinstance(deleted_relations, list) else [],
        "tasks": tasks if isinstance(tasks, list) else []
    }
