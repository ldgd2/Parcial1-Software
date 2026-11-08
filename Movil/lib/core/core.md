# Estructura de Core (Núcleo)

La carpeta `core` es el pilar central de la aplicación. Contiene la configuración global, la arquitectura base, los sistemas de diseño y los servicios fundamentales que mantienen la aplicación funcionando en su nivel más bajo. No contiene lógica de negocio específica de ninguna funcionalidad, sino que provee las herramientas necesarias para que los módulos funcionen correctamente.

## Árbol de Directorios

```text
└── core/
    ├── network/                       
    │   ├── api_provider.dart            
    │   └── interceptors/              
    │       └── auth_interceptor.dart  
    ├── theme/                         
    │   ├── app_theme.dart             
    │   ├── app_colors.dart            
    │   └── app_text_styles.dart       
    ├── routes/                        
    │   └── app_router.dart            
    ├── errors/                        
    │   ├── exceptions.dart            
    │   └── failure.dart               
    ├── storage/                       
    │   └── local_storage_service.dart 
    ├── constants/                     
    │   └── app_constants.dart         
    ├── sync/                          
    │   ├── offline_manager.dart       
    │   └── sync_queue.dart            
    └── ai/                            
        ├── text/
        │   ├── text_ai_engine.dart       
        │   └── text_prompt_templates.dart      
        ├── vision/
        │   └── vision_ai_engine.dart      
        └── voice/
            └── voice_ai_engine.dart      
```

## Detalle de Capas

### 1. Red (`network/`)
Configuración centralizada para la comunicación HTTP. Provee una base estructurada para facilitar las peticiones, evitando redundancia en la configuración.
- **`api_provider.dart`**: Clase padre o envoltorio (wrapper) que mapea y simplifica los métodos HTTP (GET, POST, PUT, DELETE). Centraliza la configuración (timeouts, baseUrl) y el mapeo de respuestas/errores, permitiendo que los servicios de cada módulo solo tengan que consumirla pasando el path específico.
- **`interceptors/`**: Modificadores de peticiones globales, por ejemplo, inyección de tokens de autenticación o refresco de tokens (`auth_interceptor.dart`).

### 2. Tema y Diseño (`theme/`)
Definición del sistema de diseño (Design System) de la aplicación.
- **`app_theme.dart`**: Configuración unificada de `ThemeData` para la app (incluyendo modo claro y oscuro).
- **`app_colors.dart`**: Paleta de colores global y semántica de la aplicación.
- **`app_text_styles.dart`**: Estilos de tipografía estandarizados para asegurar coherencia en todos los módulos.

### 3. Navegación de Pantallas (`routes/`)
Gestión centralizada del enrutamiento de la UI (Interfaces, no endpoints de API). Sigue el principio de delegación para evitar archivos gigantes y mantener el archivo `main.dart` totalmente limpio.
- **`app_router.dart`**: Es el orquestador principal de la navegación. Al centralizar esto, permite que `main.dart` funcione únicamente como un **lanzador** sin lógica compleja. Cuando la app necesita cambiar de pantalla, simplemente llama a métodos estáticos de este orquestador (ej. `AppRouter.irAlHome()`), haciendo que la navegación sea directa y de 1 sola línea. Internamente, este router importa y orquesta las rutas que cada módulo definió previamente.

### 4. Manejo de Errores (`errors/`)
Clases y utilidades para estandarizar cómo se representan los errores y fallos en toda la aplicación.
- **`exceptions.dart`**: Excepciones personalizadas puras que ocurren en el nivel de datos (ej. `ServerException`, `CacheException`).
- **`failure.dart`**: Entidades genéricas para representar errores de forma controlada hacia la capa de presentación, normalmente usadas en arquitecturas limpias (ej. `ServerFailure`).

### 5. Almacenamiento Local (`storage/`)
Interfaces y servicios globales para acceder al almacenamiento persistente del dispositivo.
- **`local_storage_service.dart`**: Manejador y configurador para SharedPreferences, Flutter Secure Storage, o bases de datos locales (Hive/SQLite/Isar) para persistir datos como sesión, preferencias, etc.

### 6. Constantes Globales (`constants/`)
Valores fijos o enumeraciones que se aplican a nivel de toda la app.
- **`app_constants.dart`**: Claves genéricas, nombre de la aplicación, duraciones de animaciones por defecto o links globales.

### 7. Sincronización Offline (`sync/`)
Maneja el comportamiento "offline-first" de la aplicación, permitiendo que el usuario siga operando sin internet.
- **`offline_manager.dart`**: Monitoriza activamente el estado de la conexión a la red.
- **`sync_queue.dart`**: Encola de forma segura las acciones y peticiones (crear, actualizar, eliminar) cuando el dispositivo está desconectado. Una vez que se restablece la conexión, envía automáticamente todas las peticiones pendientes de la cola hacia el servidor.

### 8. Inteligencia Artificial Local (`ai/`)
Encapsula los motores y herramientas para ejecutar procesos de Inteligencia Artificial directamente en el dispositivo. Se divide en sub-carpetas para no amontonar código y mantener una alta escalabilidad.
- **`text/`**: Modelos de lenguaje (LLMs) locales para procesamiento de texto, con su motor (`text_ai_engine.dart`) y sus propias plantillas (`text_prompt_templates.dart`).
- **`vision/`**: Modelos locales de visión computacional para procesar o reconocer imágenes (`vision_ai_engine.dart`).
- **`voice/`**: Modelos de transcripción de voz a texto o generación de voz (`voice_ai_engine.dart`).
