import os
import httpx
from backend.core.config import settings

def mapear_tipo_sql(tipo_java: str) -> str:
    """Mapea tipos genéricos a tipos de PostgreSQL"""
    tipo_java = tipo_java.lower()
    if 'int' in tipo_java:
        return 'INTEGER'
    elif 'long' in tipo_java:
        return 'BIGINT'
    elif 'bool' in tipo_java:
        return 'BOOLEAN'
    elif 'float' in tipo_java or 'double' in tipo_java:
        return 'DOUBLE PRECISION'
    elif 'date' in tipo_java or 'time' in tipo_java:
        return 'TIMESTAMP'
    else:
        return 'VARCHAR(255)'

def generar_tablas_basicas(nodos: list) -> str:
    sql = ""
    for nodo in nodos:
        if nodo.get("type") in ["class", "interface"]:
            nombre = nodo.get("nombre", "").lower() + "s"
            sql += f"CREATE TABLE {nombre} (\n"
            atributos = nodo.get("atributos", [])
            cols = []
            
            # Siempre aseguramos que haya una PK
            tiene_pk = False
            for attr in atributos:
                nombre_attr = attr.get("nombre", "").lower()
                tipo_sql = mapear_tipo_sql(attr.get("tipo", "string"))
                
                if attr.get("visibilidad") == 'PK':
                    cols.append(f"    {nombre_attr} UUID PRIMARY KEY")
                    tiene_pk = True
                else:
                    cols.append(f"    {nombre_attr} {tipo_sql}")
            
            if not tiene_pk:
                cols.insert(0, "    id UUID PRIMARY KEY")
                
            sql += ",\n".join(cols)
            sql += "\n);\n\n"
    return sql

async def solicitar_constraints_ia(nodos: list, relaciones: list) -> str:
    """
    Envía las relaciones y tablas a la IA para que infiera las FK o tablas intermedias (N:M).
    """
    if not relaciones:
        return ""
        
    prompt = f"""
    Eres un experto en bases de datos PostgreSQL.
    A continuación, tienes un conjunto de nodos (tablas) y relaciones entre ellos.
    
    Nodos: {[{'id': n['id'], 'nombre': n['nombre']} for n in nodos if n.get('type') in ['class', 'interface']]}
    Relaciones: {relaciones}
    
    Genera ÚNICAMENTE las sentencias SQL (ALTER TABLE ADD CONSTRAINT o CREATE TABLE para N:M)
    necesarias para mapear estas relaciones. 
    Asume que todas las tablas terminan en 's' y su PK principal es de tipo UUID.
    No incluyas formato Markdown, explicaciones, ni etiquetas de código. SOLO el SQL válido.
    """
    
    headers = {
        "Authorization": f"Bearer {settings.IA_API}",
        "Content-Type": "application/json"
    }
    
    # URL base para OpenRouter (se puede cambiar a Gemini u otro proveedor configurado en IA_SERVICE)
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={
                "model": settings.IA_MODEL,
                "messages": [{"role": "user", "content": prompt}]
            }, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            else:
                print(f"Error IA SQL: {response.text}")
                return "-- Error al generar relaciones complejas\n"
    except Exception as e:
        print(f"Excepción IA SQL: {str(e)}")
        return "-- Fallo en la conexión a la IA para las relaciones\n"

async def generar_migracion_sql(diagram_json: dict, temp_dir: str):
    """
    Genera el archivo V1__Esquema_Inicial.sql usando lógica determinista para tablas
    y apoyándose en la IA para las relaciones abstractas.
    """
    nodos = diagram_json.get("nodes", [])
    relaciones = diagram_json.get("relations", [])
    
    sql_script = "-- Migración autogenerada por IA\n\n"
    sql_script += generar_tablas_basicas(nodos)
    
    sql_relaciones = await solicitar_constraints_ia(nodos, relaciones)
    sql_script += "\n-- Constraints inferidos por IA\n"
    sql_script += sql_relaciones
    
    # Limpiamos posibles formatos markdown que la IA haya filtrado por error
    sql_script = sql_script.replace("```sql", "").replace("```", "")
    
    file_path = os.path.join(temp_dir, "src", "main", "resources", "db", "migration", "V1__Esquema_Inicial.sql")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(sql_script)
