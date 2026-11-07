import copy
from typing import Any, Dict, List, Optional
from backend.modules.gestion_interoperabilidad.detectar_errores_xml.schemas.response import CorregirErroresResponse
from backend.modules.gestion_interoperabilidad.detectar_errores_xml.services.detector_service import (
    analizar_errores_logicos_bd,
    _tiene_pk,
    _obtener_tipo_pk,
    _extraer_nombre_tipo_attr,
    SQL_RESERVED_WORDS
)


async def corregir_logica_bd(
    xml_content: Optional[str] = None,
    nodes: Optional[List[Dict[str, Any]]] = None,
    relations: Optional[List[Dict[str, Any]]] = None,
    errores_ids: Optional[List[str]] = None
) -> CorregirErroresResponse:
    # 1. Analizar estado actual
    reporte = await analizar_errores_logicos_bd(
        xml_content=xml_content,
        nodes=nodes,
        relations=relations
    )

    if reporte.total_errores == 0:
        return CorregirErroresResponse(
            resumen="El diseño ya es consistente, no requirió modificaciones.",
            errores_corregidos=0,
            fixed_nodes=nodes or [],
            fixed_relations=relations or [],
            fixed_xml=xml_content
        )

    fixed_nodes = copy.deepcopy(nodes or [])
    fixed_relations = copy.deepcopy(relations or [])

    table_name_map = {}
    for n in fixed_nodes:
        name = str(n.get("name") or n.get("nombre") or "").strip()
        table_name_map[name.lower()] = n
        table_name_map[str(n.get("id", "")).lower()] = n

    corregidos_count = 0
    nuevas_tablas_intermedias = []
    relaciones_a_eliminar = set()
    nuevas_relaciones = []

    # 2. Iterar sobre los errores detectados y subsanar
    for err in reporte.errores:
        if errores_ids and err.id not in errores_ids:
            continue

        # A. Sin Clave Primaria (PK)
        if err.tipo == "sin_pk":
            target_n = table_name_map.get(err.tabla.lower())
            if target_n:
                attrs = target_n.get("attributes") or target_n.get("atributos") or []
                if not _tiene_pk(target_n):
                    if isinstance(attrs, list) and len(attrs) > 0 and isinstance(attrs[0], dict):
                        attrs.insert(0, {"nombre": "id", "tipo": "int", "visibilidad": "+", "isPk": True})
                    else:
                        attrs.insert(0, "+id:int")
                    target_n["attributes"] = attrs
                    target_n["atributos"] = attrs
                    corregidos_count += 1

        # B. Palabra reservada SQL
        elif err.tipo == "palabra_reservada":
            target_n = table_name_map.get(err.tabla.lower())
            if target_n:
                if err.columna:
                    attrs = target_n.get("attributes") or target_n.get("atributos") or []
                    new_attrs = []
                    for a in attrs:
                        name, dtype, es_fk = _extraer_nombre_tipo_attr(a)
                        if name.lower() == err.columna.lower():
                            safe_name = f"{name}_val"
                            new_attrs.append(f"+{safe_name}:{dtype}" if isinstance(a, str) else {**a, "nombre": safe_name})
                        else:
                            new_attrs.append(a)
                    target_n["attributes"] = new_attrs
                    target_n["atributos"] = new_attrs
                    corregidos_count += 1
                else:
                    safe_table_name = f"{err.tabla.capitalize()}Entity"
                    target_n["name"] = safe_table_name
                    target_n["nombre"] = safe_table_name
                    corregidos_count += 1

        # C. Tipo discordante en FK
        elif err.tipo == "tipo_discordante":
            target_n = table_name_map.get(err.tabla.lower())
            if target_n and err.columna:
                attrs = target_n.get("attributes") or target_n.get("atributos") or []
                new_attrs = []
                for a in attrs:
                    name, dtype, es_fk = _extraer_nombre_tipo_attr(a)
                    if name.lower() == err.columna.lower():
                        new_attrs.append(f"+*{name}:int" if isinstance(a, str) else {**a, "tipo": "int"})
                    else:
                        new_attrs.append(a)
                target_n["attributes"] = new_attrs
                target_n["atributos"] = new_attrs
                corregidos_count += 1

        # D. Relación N:M directa -> Transformar en Tabla Intermedia Asociativa
        elif err.tipo == "relacion_nm_directa":
            # Identificar las dos tablas y la relación
            s_name = err.tabla
            t_match = err.columna.replace("Relación N:M con ", "").strip() if err.columna else ""
            if s_name and t_match:
                join_table_name = f"{s_name}_{t_match}"
                # Evitar duplicar tabla asociativa si ya se creó
                if not any((n.get("name") or n.get("nombre")) == join_table_name for n in fixed_nodes):
                    fk1_col = f"{s_name.lower()}_id"
                    fk2_col = f"{t_match.lower()}_id"

                    nueva_asociativa = {
                        "id": f"node_{join_table_name.lower()}",
                        "name": join_table_name,
                        "nombre": join_table_name,
                        "type": "class",
                        "attributes": ["+id:int", f"+*{fk1_col}:int", f"+*{fk2_col}:int", "+@fecha_creacion:date"],
                        "methods": [],
                        "x": 300,
                        "y": 300
                    }
                    nuevas_tablas_intermedias.append(nueva_asociativa)

                    # Crear dos relaciones 1..* hacia la asociativa
                    nuevas_relaciones.append({
                        "id": f"rel_{s_name}_{join_table_name}",
                        "sourceId": s_name,
                        "targetId": join_table_name,
                        "type": "association",
                        "label": "1..*"
                    })
                    nuevas_relaciones.append({
                        "id": f"rel_{t_match}_{join_table_name}",
                        "sourceId": t_match,
                        "targetId": join_table_name,
                        "type": "association",
                        "label": "1..*"
                    })

                    # Marcar relación N:M original para ser eliminada
                    for idx_r, r in enumerate(fixed_relations):
                        src = str(r.get("sourceId") or r.get("source") or "")
                        tgt = str(r.get("targetId") or r.get("target") or "")
                        if (src.lower() == s_name.lower() and tgt.lower() == t_match.lower()) or (src.lower() == t_match.lower() and tgt.lower() == s_name.lower()):
                            relaciones_a_eliminar.add(idx_r)

                    corregidos_count += 1

        # E. FK Huérfana o Tabla destino faltante
        elif err.tipo == "fk_huerfana":
            if err.columna:
                # Si es un atributo de FK huérfano, crear la entidad faltante básica
                missing_name = err.columna.replace("_id", "").capitalize()
                if missing_name and missing_name.lower() not in table_name_map:
                    nueva_entidad = {
                        "id": f"node_{missing_name.lower()}",
                        "name": missing_name,
                        "nombre": missing_name,
                        "type": "class",
                        "attributes": ["+id:int", "+nombre:string"],
                        "methods": [],
                        "x": 150,
                        "y": 150
                    }
                    nuevas_tablas_intermedias.append(nueva_entidad)
                    table_name_map[missing_name.lower()] = nueva_entidad

                    nuevas_relaciones.append({
                        "id": f"rel_{missing_name}_{err.tabla}",
                        "sourceId": missing_name,
                        "targetId": err.tabla,
                        "type": "association",
                        "label": "1..*"
                    })
                    corregidos_count += 1

        # F. Tabla Aislada -> Conectar a la primera entidad maestra disponible (ej. Usuario o Curso)
        elif err.tipo == "tabla_aislada":
            master_candidate = next((n.get("name") or n.get("nombre") for n in fixed_nodes if (n.get("name") or n.get("nombre")) not in [err.tabla, None]), None)
            if master_candidate:
                nuevas_relaciones.append({
                    "id": f"rel_{master_candidate}_{err.tabla}_auto",
                    "sourceId": master_candidate,
                    "targetId": err.tabla,
                    "type": "association",
                    "label": "1..*"
                })
                corregidos_count += 1

    # Aplicar agregaciones y podas
    fixed_nodes.extend(nuevas_tablas_intermedias)
    fixed_relations = [r for idx, r in enumerate(fixed_relations) if idx not in relaciones_a_eliminar]
    fixed_relations.extend(nuevas_relaciones)

    # Re-generar XML sincronizado
    fixed_xml = None
    if xml_content:
        try:
            from backend.modules.gestion_interoperabilidad.exportar_a_xml.services.export_service import exportar_a_xmi
            fixed_xml = exportar_a_xmi(fixed_nodes, fixed_relations)
        except Exception as xmi_err:
            print(f"[CorrectorBD] No se pudo re-exportar a XML: {xmi_err}")
            fixed_xml = xml_content

    return CorregirErroresResponse(
        resumen=f"Se corrigieron exitosamente {corregidos_count} inconsistencias lógicas en el esquema de base de datos.",
        errores_corregidos=corregidos_count,
        fixed_nodes=fixed_nodes,
        fixed_relations=fixed_relations,
        fixed_xml=fixed_xml
    )

