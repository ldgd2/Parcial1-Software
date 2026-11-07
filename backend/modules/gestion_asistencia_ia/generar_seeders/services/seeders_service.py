from typing import Any, Dict, List
from backend.modules.gestion_asistencia_ia.generar_seeders.schemas.response import GenerarSeedersResponse
from backend.modules.gestion_asistencia_ia.generar_seeders.services.topological_sorter import ordenar_topologicamente
from backend.modules.gestion_asistencia_ia.generar_seeders.services.sql_seeder_builder import construir_seeders_sql
from backend.modules.gestion_asistencia_ia.generar_seeders.services.java_runner_builder import construir_java_runner


def generar_script_seeders(
    nodes: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
    cantidad_por_tabla: int = 10,
    formato: str = "sql"
) -> GenerarSeedersResponse:
    """
    Coordina la generación de seeders relacionales deterministas y randomizados
    para Spring Boot y PostgreSQL sin requerir llamadas a IA.
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

    # 1. Ordenamiento topológico
    orden_tablas = ordenar_topologicamente(nodes, relations)
    orden_nombres = [str(n.get("name") or n.get("nombre")) for n in orden_tablas]

    # 2. Construcción del dataset SQL con integridad referencial
    final_sql, _, registros_por_tabla, total_registros = construir_seeders_sql(
        orden_tablas=orden_tablas,
        cantidad_por_tabla=cantidad_por_tabla
    )

    # 3. Construcción del Runner Java si se solicita
    java_runner_code = None
    if formato in ["java", "java_runner"]:
        java_runner_code = construir_java_runner()

    resumen_text = (
        f"Se generaron {total_registros} registros relacionales para {len(orden_tablas)} tablas, "
        f"respetando el orden topológico de dependencias e integridad de claves foráneas."
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
