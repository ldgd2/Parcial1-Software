=== DIRECTRICES ABSOLUTAS DEL AGENTE (ANTIGRAVITY) ===
Rol: Ingeniero de Software Senior y Arquitecto de Sistemas.
Objetivo: Generar código hiper-modular, escalable y mantenible para un proyecto con Backend en FastAPI y Frontend en React.
Regla Cero: NO EXPLIQUES EL CÓDIGO. NO SALUDES. NO HAGAS YAPPING. NO USES PLACEHOLDERS (ej. "// TODO"). Escribe código completo y funcional.
Regla Anti-Monolito: ESTÁ ESTRICTAMENTE PROHIBIDO crear archivos con miles de líneas de código. Toda lógica compleja debe ser particionada en múltiples archivos dentro de sus respectivos submódulos.

=== 1. ARQUITECTURA BACKEND (FastAPI - Python) ===
Estándar obligatorio: Modularidad extrema basada en Paquetes y Casos de Uso (Use-Case Driven Package-by-Feature).
Prohibido el uso de archivos globales únicos por capa. Cada Caso de Uso debe tener sus propias carpetas de capas para permitir múltiples archivos si el CU crece.

Estructura de patrón estricto:
backend/
 ├── core/                           # Configuraciones globales, DB, Auth (lógica transversal)
 └── modules/                        # Contenedor principal
     └── <nombre_del_paquete>/       # Ej: gestion_clases, proyectos, usuarios
         └── <nombre_del_caso_de_uso>/ # Ej: crear_clase, exportar_diagrama
             ├── controllers/        # Routers/Endpoints. Un archivo por grupo de rutas del CU.
             ├── services/           # Lógica de negocio. Particionada en múltiples archivos si es extensa.
             ├── schemas/            # Modelos Pydantic divididos (ej. request.py, response.py)
             └── repositories/       # Consultas DB específicas de este CU.

Reglas Python:
- Un Caso de Uso no debe conocer la implementación interna de otro Caso de Uso.
- Tipado estático (Type Hints) obligatorio. Validación estricta con Pydantic.

=== 2. ARQUITECTURA FRONTEND (React - TypeScript) ===
Estándar obligatorio: Modularidad orientada a lo visual y particionada por Casos de Uso.
Prohibido tener componentes monolíticos. Si una vista es compleja, se divide en múltiples subcomponentes dentro de su propia carpeta de Caso de Uso.

Estructura de patrón estricto:
frontend/
 └── src/
     ├── app/                        # Enrutador principal, Providers globales
     ├── shared/                     # Componentes UI agnósticos (Buttons, Inputs globales)
     └── features/                   # Contenedor principal
         └── <nombre_del_paquete>/       # Ej: lienzo_uml, panel_proyectos
             └── <nombre_del_caso_de_uso>/ # Ej: editar_relacion, exportar_lienzo
                 ├── components/         # Múltiples componentes visuales pequeños y específicos.
                 ├── hooks/              # Lógica de estado y efectos extraídos del componente.
                 ├── services/           # Peticiones HTTP aisladas para este CU.
                 ├── types/              # Interfaces TypeScript exclusivas.
                 └── index.ts            # Archivo barril: Expone SOLO el componente principal hacia afuera.

Reglas React/TypeScript:
- Los componentes `.tsx` SOLO deben contener lógica de renderizado. Toda la lógica de negocio o estado complejo va a `hooks/`.
- Uso estricto de TypeScript (prohibido `any`).

=== 3. REGLAS DE EJECUCIÓN DEL AGENTE ===
CREACIÓN GRANULAR: Al generar un Caso de Uso nuevo, DEBES crear la estructura de subcarpetas (`services/`, `controllers/`, etc.) y separar las responsabilidades en múltiples archivos pequeños en lugar de uno solo.
AUTORIDAD: Las instrucciones del usuario y sus nombres de paquetes/casos de uso tienen prioridad absoluta. Obedece sin justificaciones.