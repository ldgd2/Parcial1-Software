"""
Migración Flyway V1 del backend generado.

Todo es DETERMINISTA (antes las FK las escribía una IA y en producción rompía el arranque: copiaba el
nombre de ejemplo `fk_tu_nombre_unico` y apuntaba una columna INTEGER a un id UUID, Flyway abortaba y
Spring Boot moría -> 502).

Los nombres salen con las MISMAS reglas que las entidades JPA (parser_service):
  - tabla   = nombre de la clase sin símbolos, en minúsculas, + "s"
  - columna = sanitize_identifier(atributo) en minúsculas     (id_cliente -> idcliente)
  - id      = UUID (BaseEntity); los atributos PK/FK también son UUID, porque referencian ids UUID.
Cada FK va dentro de un bloque con EXCEPTION: si algo no encaja se registra un aviso y la app arranca.
"""
import os
import re
from typing import Dict, List, Optional

from backend.modules.gestion_asistencia_ia.exportar_github.services.parser_service import sanitize_identifier

_AUDITORIA = {"id", "createdat", "updatedat", "isactive"}
# Relaciones que no generan claves foráneas
_SIN_FK = {"inheritance", "realization", "dependency", "usage", "trace", "abstraction", "substitution",
           "information_flow", "instantiate", "instantiated_by", "template_binding", "calls", "called_by",
           "create", "send", "assembly", "connector", "delegate"}


def nombre_tabla(raw_nombre: str) -> str:
    """Igual que parser_service: 'Detalle_Pedido' -> 'detallepedidos'."""
    base = re.sub(r"[^a-zA-Z0-9]", "", str(raw_nombre or "")).lower() or "entidad"
    return base if base.endswith("s") else f"{base}s"


def nombre_columna(raw_attr: str) -> str:
    """Igual que la entidad JPA: @Column(name = sanitize_identifier(x).lower())."""
    return sanitize_identifier(raw_attr).lower()


def clean_sql_identifier(raw_name: str, default: str = "attr") -> str:
    """Compatibilidad: identificador SQL válido a partir de un nombre UML."""
    if not raw_name:
        return default
    name = re.sub(r'^[\-\+\#\~\s]+', '', str(raw_name))
    if ':' in name:
        name = name.split(':')[0]
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name).strip('_').lower()
    if not name:
        return default
    if name[0].isdigit():
        name = f"{default}_{name}"
    return name


def mapear_tipo_sql(tipo_java: str) -> str:
    """Mapea tipos genéricos a tipos de PostgreSQL"""
    tipo_java = str(tipo_java).lower().strip()
    if 'uuid' in tipo_java:
        return 'UUID'
    if 'long' in tipo_java:
        return 'BIGINT'
    if 'int' in tipo_java or 'entero' in tipo_java:
        return 'INTEGER'
    if 'bool' in tipo_java or 'logico' in tipo_java:
        return 'BOOLEAN'
    if 'float' in tipo_java or 'double' in tipo_java or 'decimal' in tipo_java:
        return 'DOUBLE PRECISION'
    if 'datetime' in tipo_java or 'timestamp' in tipo_java:
        return 'TIMESTAMP'
    if 'date' in tipo_java or 'fecha' in tipo_java:
        return 'DATE'
    if 'time' in tipo_java:
        return 'TIME'
    return 'VARCHAR(255)'


def _nombre(n: dict) -> str:
    return str(n.get("nombre") or n.get("name") or "")


def _clases(nodos: list) -> list:
    return [n for n in (nodos or []) if str(n.get("type") or "class").lower() in ("class", "interface", "clase", "table", "entity")]


def _columnas(nodo: dict) -> List[dict]:
    """[{col, tipo_sql, es_ref, raw}] sin id ni auditoría, sin duplicados."""
    cols, vistos = [], set()
    for attr in (nodo.get("atributos") or nodo.get("attributes") or []):
        if not isinstance(attr, dict):
            attr = {"nombre": str(attr)}
        raw = attr.get("nombre") or attr.get("name") or ""
        col = nombre_columna(raw)
        if col in _AUDITORIA or col in vistos or col == "unnamed":
            continue
        vistos.add(col)
        raw_tipo = attr.get("tipo") or attr.get("type") or ""
        if not raw_tipo and ':' in str(raw):
            raw_tipo = str(raw).split(':', 1)[1].strip()
        es_ref = str(attr.get("visibilidad") or "").upper() in ("PK", "FK")
        cols.append({"col": col, "tipo_sql": "UUID" if es_ref else mapear_tipo_sql(raw_tipo or "string"),
                     "es_ref": es_ref, "raw": str(raw)})
    return cols


def generar_tablas_basicas(nodos: list) -> str:
    sql = 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";\n\n'
    sql += '''CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';\n\n'''

    for nodo in _clases(nodos):
        tabla = nombre_tabla(_nombre(nodo))
        cols = _columnas(nodo)
        lineas = ["    id UUID PRIMARY KEY DEFAULT gen_random_uuid()"]
        lineas += [f"    {c['col']} {c['tipo_sql']}" for c in cols]
        lineas += ["    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP",
                   "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP",
                   "    is_active BOOLEAN DEFAULT TRUE"]
        sql += f"CREATE TABLE IF NOT EXISTS {tabla} (\n" + ",\n".join(lineas) + "\n);\n\n"

        sql += f"DROP TRIGGER IF EXISTS update_{tabla}_updated_at ON {tabla};\n"
        sql += f"CREATE TRIGGER update_{tabla}_updated_at\nBEFORE UPDATE ON {tabla}\n"
        sql += "FOR EACH ROW\nEXECUTE FUNCTION update_updated_at_column();\n\n"

        # Columnas nuevas en tablas que ya existían
        for c in cols:
            sql += f"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS {c['col']} {c['tipo_sql']};\n"
        sql += "\n"
    return sql


def _destino_por_nombre(col: str, tablas: Dict[str, str]) -> Optional[str]:
    """idcliente / clienteid / id_cliente -> tabla 'clientes' si existe."""
    base = col
    for pref in ("id_", "id"):
        if base.startswith(pref) and len(base) > len(pref):
            cand = base[len(pref):].strip("_")
            if cand in tablas:
                return tablas[cand]
    for suf in ("_id", "id"):
        if base.endswith(suf) and len(base) > len(suf):
            cand = base[:-len(suf)].strip("_")
            if cand in tablas:
                return tablas[cand]
    return None


def _bloque_fk(tabla: str, columna: str, destino: str, usados: set) -> str:
    nombre = f"fk_{tabla}_{columna}"[:60]
    i = 2
    while nombre in usados:
        nombre = f"fk_{tabla}_{columna}"[:57] + f"_{i}"
        i += 1
    usados.add(nombre)
    return f"""DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{nombre}') THEN
        ALTER TABLE {tabla} ADD CONSTRAINT {nombre} FOREIGN KEY ({columna}) REFERENCES {destino} (id) ON DELETE SET NULL;
    END IF;
EXCEPTION WHEN others THEN
    RAISE NOTICE 'No se creó la FK {nombre}: %', SQLERRM;
END $$;
"""


def referencias(nodos: list, relaciones: list) -> Dict[str, Dict[str, str]]:
    """{tabla: {columna: tabla_destino}} para cada atributo PK/FK que referencia a otra clase
    (por su nombre, p. ej. id_cliente -> clientes, o por la única relación dibujada que le queda)."""
    clases = _clases(nodos)
    por_id = {str(n.get("id")): n for n in clases}
    tablas = {}
    for n in clases:
        t = nombre_tabla(_nombre(n))
        tablas[re.sub(r"[^a-zA-Z0-9]", "", _nombre(n)).lower()] = t
        tablas[t] = t

    vecinos: Dict[str, List[str]] = {}
    for r in relaciones or []:
        tipo = str(r.get("type") or r.get("tipo") or "").lower()
        if tipo in _SIN_FK:
            continue
        a = por_id.get(str(r.get("sourceId") or r.get("source") or r.get("origen") or ""))
        b = por_id.get(str(r.get("targetId") or r.get("target") or r.get("destino") or ""))
        if not a or not b:
            continue
        ta, tb = nombre_tabla(_nombre(a)), nombre_tabla(_nombre(b))
        vecinos.setdefault(ta, []).append(tb)
        vecinos.setdefault(tb, []).append(ta)

    res: Dict[str, Dict[str, str]] = {}
    for n in clases:
        tabla = nombre_tabla(_nombre(n))
        refs = [c for c in _columnas(n) if c["es_ref"]]
        candidatos = [v for v in dict.fromkeys(vecinos.get(tabla, [])) if v != tabla]
        sin_destino = []
        for c in refs:
            destino = _destino_por_nombre(c["col"], tablas)
            if destino:
                res.setdefault(tabla, {})[c["col"]] = destino
                if destino in candidatos:
                    candidatos.remove(destino)
            else:
                sin_destino.append(c)
        # Un único atributo FK sin nombre reconocible y una única relación pendiente: es esa
        if len(sin_destino) == 1 and len(candidatos) == 1:
            res.setdefault(tabla, {})[sin_destino[0]["col"]] = candidatos[0]
    return res


def generar_claves_foraneas(nodos: list, relaciones: list) -> str:
    """FK para cada atributo PK/FK que referencia a otra clase."""
    sql, usados = "", set()
    for tabla, cols in referencias(nodos, relaciones).items():
        for col, destino in cols.items():
            sql += _bloque_fk(tabla, col, destino, usados)
    return sql


async def generar_migracion_sql(diagram_json: dict, temp_dir: str):
    """Genera src/main/resources/db/migration/V1__Esquema_Inicial.sql (sin IA)."""
    nodos = diagram_json.get("nodes", [])
    relaciones = diagram_json.get("edges", []) or diagram_json.get("relations", [])

    sql_script = "-- Migración autogenerada a partir del diagrama\n\n"
    sql_script += generar_tablas_basicas(nodos)
    fks = generar_claves_foraneas(nodos, relaciones)
    if fks:
        sql_script += "\n-- Claves foráneas (atributos PK/FK del diagrama)\n" + fks

    file_path = os.path.join(temp_dir, "src", "main", "resources", "db", "migration", "V1__Esquema_Inicial.sql")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(sql_script)
