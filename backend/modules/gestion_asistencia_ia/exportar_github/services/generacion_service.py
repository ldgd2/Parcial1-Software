import os
import tempfile
import uuid

from backend.modules.gestion_asistencia_ia.exportar_github.services.parser_service import parsear_diagrama
from backend.modules.gestion_asistencia_ia.exportar_github.services.migrations_service import generar_migracion_sql
from backend.modules.gestion_asistencia_ia.exportar_github.services.ia_injection_service import inyectar_logica_ia

async def generar_spring_boot(diagram_json: dict, nombre_repo: str = "proyecto_db") -> str:
    """
    Orquesta las 3 Fases del motor de generación IA:
    1. Parser Determinista (Jinja2)
    2. Motor de Migraciones (SQL/Flyway)
    3. Cirugía de Código (IA Injection)
    
    Retorna la ruta de la carpeta temporal donde se guardó el código.
    """
    # Directorio temporal atado al procesamiento actual
    temp_dir = tempfile.mkdtemp(prefix=f"proyecto_ia_{uuid.uuid4().hex[:8]}_")
    
    # Fase 1: Parsing
    parsear_diagrama(diagram_json, temp_dir, nombre_repo)
    
    # Fase 2: SQL y Relaciones con IA
    await generar_migracion_sql(diagram_json, temp_dir)
    
    # Fase 3: Inyección de Lógica IA en Controladores/Servicios
    await inyectar_logica_ia(temp_dir)
    
    # El código resultante en temp_dir ya es funcional y listo para Git Push
    return temp_dir
