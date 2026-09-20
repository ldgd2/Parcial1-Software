import os
import re
import httpx
from backend.core.config import settings

def clean_sql_identifier(raw_name: str, default: str = "attr") -> str:
    """Limpia un nombre UML (ej: '- email: string') para ser un identificador SQL válido."""
    if not raw_name:
        return default
    # Quitar símbolos UML iniciales: -, +, #, ~ y espacios
    name = re.sub(r'^[\-\+\#\~\s]+', '', str(raw_name))
    # Si contiene ':', tomar solo la parte anterior al tipo
    if ':' in name:
        name = name.split(':')[0]
    # Quitar cualquier carácter que no sea alfanumérico o guion bajo
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name).strip('_').lower()
    if not name:
        return default
    if name[0].isdigit():
        name = f"{default}_{name}"
    return name

def mapear_tipo_sql(tipo_java: str) -> str:
    """Mapea tipos genéricos a tipos de PostgreSQL"""
    tipo_java = str(tipo_java).lower().strip()
    if 'int' in tipo_java or 'entero' in tipo_java:
        return 'INTEGER'
    elif 'long' in tipo_java:
        return 'BIGINT'
    elif 'bool' in tipo_java or 'logico' in tipo_java:
        return 'BOOLEAN'
    elif 'float' in tipo_java or 'double' in tipo_java or 'decimal' in tipo_java:
        return 'DOUBLE PRECISION'
    elif 'date' in tipo_java or 'time' in tipo_java or 'fecha' in tipo_java:
        return 'TIMESTAMP'
    elif 'uuid' in tipo_java:
        return 'UUID'
    else:
        return 'VARCHAR(255)'

def generar_tablas_basicas(nodos: list) -> str:
    sql = 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";\n\n'
    sql += '''CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';\n\n'''

    for nodo in nodos:
        if nodo.get("type") in ["class", "interface"]:
            raw_nombre = nodo.get("nombre", "")
            nombre_tabla = clean_sql_identifier(raw_nombre, default="entidad")
            if not nombre_tabla.endswith("s"):
                nombre_tabla += "s"
                
            sql += f"CREATE TABLE IF NOT EXISTS {nombre_tabla} (\n"
            atributos = nodo.get("atributos", [])
            cols = []
            
            # Siempre aseguramos que haya una PK
            tiene_pk = False
            for attr in atributos:
                raw_attr_name = attr.get("nombre", "")
                nombre_attr = clean_sql_identifier(raw_attr_name, default="columna")
                
                # Ignorar columnas base de auditoría para manejarlas centralizadamente
                if nombre_attr in ['created_at', 'createdat', 'updated_at', 'updatedat', 'is_active', 'isactive']:
                    continue

                raw_tipo = attr.get("tipo", "")
                if not raw_tipo and ':' in str(raw_attr_name):
                    parts = str(raw_attr_name).split(':', 1)
                    raw_tipo = parts[1].strip()
                    
                tipo_sql = mapear_tipo_sql(raw_tipo or "string")
                
                if attr.get("visibilidad") == 'PK' or nombre_attr == 'id':
                    cols.append(f"    {nombre_attr} UUID PRIMARY KEY DEFAULT gen_random_uuid()")
                    tiene_pk = True
                else:
                    cols.append(f"    {nombre_attr} {tipo_sql}")
            
            if not tiene_pk:
                cols.insert(0, "    id UUID PRIMARY KEY DEFAULT gen_random_uuid()")
                
            cols.append("    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
            cols.append("    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
            cols.append("    is_active BOOLEAN DEFAULT TRUE")

            sql += ",\n".join(cols)
            sql += "\n);\n\n"

            # Trigger para actualizar automaticamente updated_at
            sql += f"DROP TRIGGER IF EXISTS update_{nombre_tabla}_updated_at ON {nombre_tabla};\n"
            sql += f"CREATE TRIGGER update_{nombre_tabla}_updated_at\n"
            sql += f"BEFORE UPDATE ON {nombre_tabla}\n"
            sql += f"FOR EACH ROW\n"
            sql += f"EXECUTE FUNCTION update_updated_at_column();\n\n"

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
    
    Genera únicamente sentencias SQL seguras en PostgreSQL.
    Asume que todas las tablas terminan en 's' y su PK principal es de tipo UUID ('id').
    Para cada relación de Foreign Key (FK):
    1. Asegúrate de añadir primero la columna si no existe: `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ... UUID;`
    2. Luego añade la constraint dentro de un bloque seguro:
       `DO $$ BEGIN ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY (...) REFERENCES ...; EXCEPTION WHEN OTHERS THEN NULL; END $$;`
    No incluyas formato Markdown, explicaciones, ni etiquetas de código. SOLO el SQL válido.
    """
    
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTE_API}",
        "Content-Type": "application/json"
    }
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={
                "model": settings.IA_MODEL,
                "messages": [{"role": "user", "content": prompt}]
            }, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                raw_sql = data['choices'][0]['message']['content'].strip()
                sql_lines = []
                for line in raw_sql.splitlines():
                    ls = line.strip()
                    if not ls or ls.startswith("```") or ls.lower().startswith("here") or ls.lower().startswith("aquí"):
                        continue
                    sql_lines.append(line)
                return "\n".join(sql_lines)
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
    relaciones = diagram_json.get("edges", []) or diagram_json.get("relations", [])
    
    sql_script = "-- Migración autogenerada por IA\n\n"
    sql_script += generar_tablas_basicas(nodos)
    
    sql_relaciones = await solicitar_constraints_ia(nodos, relaciones)
    if sql_relaciones and not sql_relaciones.startswith("--"):
        sql_script += "\n-- Constraints inferidos por IA\n"
        sql_script += sql_relaciones + "\n"
        
    sql_script = sql_script.replace("```sql", "").replace("```", "")
    
    file_path = os.path.join(temp_dir, "src", "main", "resources", "db", "migration", "V1__Esquema_Inicial.sql")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(sql_script)

