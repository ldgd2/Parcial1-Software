"""
Seeders SQL coherentes con el esquema REAL del backend generado (migrations_service / entidades JPA):
  - mismas tablas y columnas (detallepedidos, idcliente…)
  - id siempre UUID; los atributos PK/FK llevan el id de un registro que EXISTE en la tabla destino
  - tablas padre antes que las hijas; en ciclos la FK queda NULL
  - cada valor ajustado al tipo de la columna (antes iban ids 1, 2… en columnas UUID y Flyway abortaba)
"""
import datetime
import random
import re
import uuid
from typing import Any, Dict, List, Tuple

from backend.modules.gestion_asistencia_ia.exportar_github.services.migrations_service import (
    _clases,
    _columnas,
    nombre_tabla,
    referencias,
)
from backend.modules.gestion_asistencia_ia.generar_seeders.services.domain_data_generators import generar_valor_campo


def sanitizar_nombre_tabla(nombre_crudo: str) -> str:
    """Mismo nombre de tabla que la entidad JPA y la migración."""
    return nombre_tabla(nombre_crudo)


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


def _fecha_aleatoria() -> datetime.datetime:
    return datetime.datetime(2026, 1, 1) + datetime.timedelta(minutes=random.randint(0, 60 * 24 * 300))


def ajustar_al_tipo(valor: Any, tipo_sql: str) -> Any:
    """Convierte el valor sugerido al tipo de la columna; si no se puede, genera uno válido."""
    try:
        if tipo_sql in ("INTEGER", "BIGINT"):
            if isinstance(valor, bool):
                return int(valor)
            return int(float(valor))
        if tipo_sql == "DOUBLE PRECISION":
            return round(float(valor), 2)
        if tipo_sql == "BOOLEAN":
            if isinstance(valor, bool):
                return valor
            return str(valor).strip().lower() in ("true", "1", "si", "sí", "t")
        if tipo_sql == "DATE":
            texto = str(valor)
            datetime.date.fromisoformat(texto[:10])
            return texto[:10]
        if tipo_sql == "TIMESTAMP":
            texto = str(valor).replace("T", " ")
            datetime.datetime.fromisoformat(texto[:19])
            return texto[:19]
        if tipo_sql == "TIME":
            texto = str(valor)
            datetime.time.fromisoformat(texto[:8])
            return texto[:8]
        if tipo_sql == "UUID":
            return str(uuid.UUID(str(valor)))
        texto = "" if valor is None else str(valor)
        return texto[:255]
    except (TypeError, ValueError):
        f = _fecha_aleatoria()
        return {
            "INTEGER": random.randint(1, 100), "BIGINT": random.randint(1, 100),
            "DOUBLE PRECISION": round(random.uniform(1, 500), 2), "BOOLEAN": random.random() < 0.8,
            "DATE": f.date().isoformat(), "TIMESTAMP": f.strftime("%Y-%m-%d %H:%M:%S"),
            "TIME": f.strftime("%H:%M:%S"), "UUID": str(uuid.uuid4()),
        }.get(tipo_sql, str(valor)[:255] if valor is not None else "")


def ordenar_por_dependencias(nodos: list, refs: Dict[str, Dict[str, str]]) -> List[dict]:
    """Padres primero (tablas referenciadas por FK); lo que forma ciclos va al final."""
    clases = _clases(nodos)
    por_tabla = {nombre_tabla(n.get("nombre", "")): n for n in clases}
    pendientes = list(por_tabla)
    orden: List[str] = []
    while pendientes:
        listos = [t for t in pendientes
                  if all(d == t or d in orden or d not in por_tabla for d in refs.get(t, {}).values())]
        if not listos:  # ciclo: se rompe con la primera pendiente (sus FK irán NULL si hace falta)
            listos = [pendientes[0]]
        for t in listos:
            orden.append(t)
            pendientes.remove(t)
    return [por_tabla[t] for t in orden]


def construir_seeders_sql(
    orden_tablas: List[Dict[str, Any]],
    cantidad_por_tabla: int = 10,
    relaciones: List[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, List[Any]], Dict[str, int], int]:
    """INSERTs idempotentes (ON CONFLICT (id) DO NOTHING) con integridad referencial real."""
    refs = referencias(orden_tablas, relaciones or [])
    orden = ordenar_por_dependencias(orden_tablas, refs)

    ids_por_tabla: Dict[str, List[str]] = {}
    registros_por_tabla: Dict[str, int] = {}
    total = 0
    lineas = [
        "-- ===========================================================================",
        "-- SEEDERS DE PRUEBA GENERADOS AUTOMÁTICAMENTE PARA SPRING BOOT / POSTGRESQL",
        f"-- Registros generados por tabla: {cantidad_por_tabla}",
        "-- Integridad referencial: las FK usan ids de registros insertados antes",
        "-- Idempotencia: ON CONFLICT (id) DO NOTHING",
        "-- ===========================================================================\n",
    ]

    for nodo in orden:
        nombre = str(nodo.get("nombre") or nodo.get("name") or "")
        tabla = nombre_tabla(nombre)
        columnas = _columnas(nodo)
        fk_tabla = refs.get(tabla, {})
        encabezado = ", ".join(['"id"'] + [f'"{c["col"]}"' for c in columnas]
                               + ['"created_at"', '"updated_at"', '"is_active"'])
        lineas.append(f"-- {nombre} (tabla {tabla})")
        ids = []
        for i in range(cantidad_por_tabla):
            fila_id = str(uuid.uuid4())
            valores = [fila_id]
            for c in columnas:
                if c["es_ref"]:
                    destino = fk_tabla.get(c["col"])
                    if destino:
                        candidatos = ids_por_tabla.get(destino) or (ids if destino == tabla else [])
                        valores.append(random.choice(candidatos) if candidatos else None)
                    else:
                        valores.append(str(uuid.uuid4()))
                    continue
                tipo_raw = c["raw"].split(":", 1)[1] if ":" in c["raw"] else c["tipo_sql"].lower()
                nombre_attr = c["raw"].split(":", 1)[0]
                try:
                    sugerido = generar_valor_campo(nombre_attr, tipo_raw.strip().lower(), i, {}, nombre, False)
                except Exception:
                    sugerido = None
                valores.append(ajustar_al_tipo(sugerido, c["tipo_sql"]))
            creado = _fecha_aleatoria()
            valores += [creado.strftime("%Y-%m-%d %H:%M:%S"), creado.strftime("%Y-%m-%d %H:%M:%S"), True]
            lineas.append(f"INSERT INTO {tabla} ({encabezado}) VALUES "
                          f"({', '.join(formatear_valor_sql(v) for v in valores)}) ON CONFLICT (id) DO NOTHING;")
            ids.append(fila_id)
        ids_por_tabla[tabla] = ids
        registros_por_tabla[nombre] = cantidad_por_tabla
        total += cantidad_por_tabla
        lineas.append("")

    return "\n".join(lineas), ids_por_tabla, registros_por_tabla, total


def sql_tolerante(sql: str) -> str:
    """Versión para Flyway: cada INSERT en su propio bloque; si uno falla se avisa y la app arranca igual."""
    salida = []
    for linea in sql.splitlines():
        if linea.startswith("INSERT INTO "):
            salida.append("DO $$ BEGIN " + linea +
                          " EXCEPTION WHEN others THEN RAISE NOTICE 'Seeder omitido: %', SQLERRM; END $$;")
        else:
            salida.append(linea)
    return "\n".join(salida) + "\n"
