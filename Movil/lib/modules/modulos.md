# Estructura de Módulos

Los módulos en este proyecto seguirán una arquitectura encapsulada, asegurando que las funcionalidades sean independientes y escalables.

## Árbol de Directorios

```text
└── modules/
    └── nombre_modulo/                     
        ├── models/                        
        │   └── entidad_model.dart         
        ├── services/                      
        │   ├── modulo_endpoints.dart      
        │   └── modulo_service.dart        
        ├── controllers/                   
        │   └── modulo_controller.dart     
        ├── views/                         
        │   ├── screens/                   
        │   │   ├── flujo_principal/       
        │   │   │   └── pantalla_inicio.dart
        │   │   └── flujo_secundario/      
        │   │       └── pantalla_detalle.dart
        │   └── widgets/                   
        │       ├── buttons/               
        │       │   └── accion_especifica_btn.dart
        │       ├── cards/                 
        │       │   └── resumen_entidad_card.dart
        │       ├── dialogs/               
        │       │   └── confirmacion_dialog.dart
        │       └── inputs/                
        │           └── buscador_especifico_input.dart
        ├── utils/                         
        │   └── modulo_constants.dart      
        └── nombre_modulo_routes.dart      
```

## Detalle de Capas

### 1. Datos (`models/`)
Clases puras que representan la información de la aplicación.
- **`entidad_model.dart`**: Define los atributos de la entidad y los métodos para mapear los datos (`fromJson` / `toJson`).

### 2. Red (`services/`)
Encargada de la comunicación externa con APIs o fuentes de datos.
- **`modulo_endpoints.dart`**: Archivo dedicado a almacenar URLs exclusivas de este módulo.
- **`modulo_service.dart`**: Gestiona las peticiones a la API y retorna los modelos correspondientes.

### 3. Lógica (`controllers/`)
Gestores de estado que coordinan la interacción entre las vistas y los servicios.
- **`modulo_controller.dart`**: Conecta la vista con el servicio, procesa la lógica de negocio y maneja los estados de carga y errores.

### 4. Interfaz de Usuario (`views/`)
Contiene todos los elementos visuales del módulo.

#### Pantallas (`screens/`)
Pantallas completas que normalmente retornan un `Scaffold`.
- **`flujo_principal/`**: Pantallas del recorrido o ruta principal del usuario (ej. `pantalla_inicio.dart`).
- **`flujo_secundario/`**: Procesos derivados o rutas alternativas (ej. configuraciones o `pantalla_detalle.dart`).

#### Componentes Visuales (`widgets/`)
Elementos de la interfaz que son exclusivos y reutilizables dentro del módulo.
- **`buttons/`**: Botones específicos de la lógica del módulo (`accion_especifica_btn.dart`).
- **`cards/`**: Tarjetas de presentación de información (`resumen_entidad_card.dart`).
- **`dialogs/`**: Modales, ventanas emergentes y alertas (`confirmacion_dialog.dart`).
- **`inputs/`**: Campos de entrada de texto con validaciones propias (`buscador_especifico_input.dart`).

### 5. Apoyo (`utils/`)
Herramientas y configuraciones locales.
- **`modulo_constants.dart`**: Define textos fijos, dimensiones predeterminadas, colores específicos o cualquier constante exclusiva del módulo.

### 6. Rutas (`nombre_modulo_routes.dart`)
Expone y define las rutas de navegación de las pantallas del módulo para que puedan ser accesibles desde el enrutador principal de la aplicación.