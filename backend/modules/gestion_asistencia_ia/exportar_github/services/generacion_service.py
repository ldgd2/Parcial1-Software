import os
import tempfile
import uuid

from backend.modules.gestion_asistencia_ia.exportar_github.services.parser_service import parsear_diagrama
from backend.modules.gestion_asistencia_ia.exportar_github.services.migrations_service import generar_migracion_sql
from backend.modules.gestion_asistencia_ia.exportar_github.services.ia_injection_service import inyectar_logica_ia
from backend.modules.gestion_asistencia_ia.generar_app_movil.services.flutter_generator_service import (
    generar_app_flutter_completa,
)


def _crear_archivos_monorepo_raiz(temp_dir: str, nombre_repo: str, url_base: str):
    nombre_display = nombre_repo.replace("_", " ").replace("-", " ").title()

    readme_content = f"""# {nombre_display} - Monorepo Fullstack

Proyecto autogenerado a partir de especificaciones y modelos UML con asistencia de Inteligencia Artificial.

## Estructura del Monorepo
```text
├── backend/    # API REST construida con Spring Boot 3, JPA/Hibernate y PostgreSQL
└── frontend/   # Aplicación Móvil construida con Flutter (Dart) para Android, iOS y Web
```

---

## 1. Backend (Spring Boot)
Servicios RESTful, persistencia y documentación Swagger.

### Requisitos
- Java 17 o superior
- Maven 3.8+ (o usar `./mvnw` incluido)
- PostgreSQL

### Ejecución
```bash
cd backend
./mvnw spring-boot:run
```
La API estará disponible en `{url_base}`.
Documentación Swagger interactiva: `{url_base}/swagger-ui.html`.

---

## 2. Frontend (Flutter Mobile App)
Aplicación móvil con navegación, formularios y cliente HTTP sincronizado con los endpoints del backend.

### Requisitos
- Flutter SDK 3.0.0 o superior
- Dart 3.0.0 o superior

### Ejecución
```bash
cd frontend
flutter pub get
flutter run
```
*Nota: Si ejecutas en un emulador Android local, el backend `localhost` se accede como `http://10.0.2.2:8080`. Puedes ajustarlo en `frontend/lib/core/config/api_config.dart`.*
"""

    gitignore_content = """# Backend (Spring Boot / Maven)
backend/target/
backend/*.log
backend/.env

# Frontend (Flutter / Dart)
frontend/.dart_tool/
frontend/build/
frontend/.flutter-plugins
frontend/.flutter-plugins-dependencies
frontend/.packages
frontend/.pub-cache/

# IDEs y Sistema Operativo
.idea/
.vscode/
*.iml
.DS_Store
Thumbs.db
"""

    with open(os.path.join(temp_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    with open(os.path.join(temp_dir, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(gitignore_content)


async def generar_spring_boot(
    diagram_json: dict,
    nombre_repo: str = "proyecto_db",
    db_password: str = "password",
    url_base: str = "http://localhost:8080",
    descripcion_proyecto: str = ""
) -> tuple[str, str]:
    """
    Orquesta la generación completa del Monorepo:
    1. /backend: Spring Boot 3 + PostgreSQL (Jinja2, Flyway SQL, Cirugía IA)
    2. /frontend: App Móvil en Flutter completa (Modelos Dart, Servicios API, Vistas CRUD, Home Dashboard)
    3. Raíz: README y .gitignore maestros
    
    Retorna (ruta_carpeta_temporal, markdown_documentacion).
    """
    temp_dir = tempfile.mkdtemp(prefix=f"proyecto_ia_{uuid.uuid4().hex[:8]}_")
    
    backend_dir = os.path.join(temp_dir, "backend")
    frontend_dir = os.path.join(temp_dir, "frontend")
    os.makedirs(backend_dir, exist_ok=True)
    os.makedirs(frontend_dir, exist_ok=True)

    # ── 1. Generación del Backend en /backend ─────────────────────────
    api_docs_md = parsear_diagrama(
        diagram_json,
        backend_dir,
        nombre_repo,
        db_password,
        url_base,
        descripcion_proyecto
    )
    await generar_migracion_sql(diagram_json, backend_dir)

    # Inyección de Seeders coherentes para pruebas en la base de datos del backend generado
    try:
        from backend.modules.gestion_asistencia_ia.generar_seeders.services.seeders_service import generar_script_seeders
        nodos = diagram_json.get("nodes", [])
        relaciones = diagram_json.get("edges", []) or diagram_json.get("relations", [])
        seeders_res = generar_script_seeders(nodos, relaciones, cantidad_por_tabla=10)
        
        mig_dir = os.path.join(backend_dir, "src", "main", "resources", "db", "migration")
        os.makedirs(mig_dir, exist_ok=True)
        seeders_path = os.path.join(mig_dir, "V2__Carga_Seeders_Prueba.sql")
        with open(seeders_path, "w", encoding="utf-8") as f:
            f.write(seeders_res.sql_script)
            
        data_sql_path = os.path.join(backend_dir, "src", "main", "resources", "data.sql")
        with open(data_sql_path, "w", encoding="utf-8") as f:
            f.write(seeders_res.sql_script)
    except Exception as seed_err:
        print(f"[GeneracionService] Advertencia al generar seeders de prueba: {seed_err}")

    await inyectar_logica_ia(backend_dir, diagram_json, descripcion_proyecto)

    # ── 2. Generación del Frontend Móvil Flutter en /frontend ─────────
    generar_app_flutter_completa(
        diagram_json=diagram_json,
        output_dir=frontend_dir,
        app_name=nombre_repo,
        api_base_url=url_base
    )

    # ── 3. Raíz Monorepo ──────────────────────────────────────────────
    _crear_archivos_monorepo_raiz(temp_dir, nombre_repo, url_base)

    return temp_dir, api_docs_md
