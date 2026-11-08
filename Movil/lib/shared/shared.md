# Estructura de Shared (Compartidos)

La carpeta `shared` contiene elementos reutilizables que actúan como **clases padre o componentes base** para toda la aplicación. Su objetivo principal es evitar la duplicación de código manteniendo una consistencia estricta. 
**Regla de oro:** Cuando un módulo necesita un widget, modelo o utilidad con un comportamiento muy específico, **llama al elemento padre de `shared` y lo envuelve/extiende** localmente en su propio módulo. Nunca se modifica directamente el componente en `shared` para adaptarlo a un solo módulo; de esta forma, se usa solo lo necesario sin afectar o romper las demás pantallas de la app.

## Árbol de Directorios

```text
└── shared/
    ├── widgets/                       
    │   ├── avatars/
    │   │   └── custom_avatar.dart
    │   ├── viewers/
    │   │   └── custom_interactive_viewer.dart
    │   │   ├── custom_button.dart (Base)
    │   │   ├── custom_button_primary.dart
    │   │   ├── custom_button_secondary.dart
    │   │   ├── custom_button_outline.dart
    │   │   ├── custom_button_text.dart
    │   │   ├── custom_button_danger.dart
    │   │   └── custom_button_icon.dart
    │   ├── pickers/                   
    │   │   ├── custom_date_range_picker.dart
    │   │   ├── custom_time_picker.dart
    │   │   └── custom_media_picker.dart
    │   ├── cards/                     
    │   │   ├── custom_card.dart (Base)
    │   │   ├── custom_card_product.dart
    │   │   ├── custom_card_stat.dart
    │   │   ├── custom_card_profile.dart
    │   │   ├── custom_card_banner.dart
    │   │   ├── custom_card_media.dart
    │   │   └── custom_card_action.dart
    │   ├── sliders/                   
    │   │   ├── custom_slider.dart (Base)
    │   │   ├── custom_range_slider.dart
    │   │   ├── custom_slider_icon.dart
    │   │   ├── custom_slider_discrete.dart
    │   │   └── custom_slider_card.dart
    │   ├── switches/                  
    │   │   ├── custom_switch.dart (Base)
    │   │   ├── custom_switch_tile.dart
    │   │   ├── custom_switch_card.dart
    │   │   ├── custom_switch_icon.dart
    │   │   └── custom_switch_async.dart
    │   ├── inputs/                    
    │   │   ├── custom_input.dart (Base)
    │   │   ├── custom_input_form.dart
    │   │   ├── custom_input_search.dart
    │   │   ├── custom_input_otp.dart
    │   │   ├── custom_input_phone.dart
    │   │   ├── custom_input_currency.dart
    │   │   ├── custom_input_textarea.dart
    │   │   ├── custom_input_password.dart
    │   │   ├── custom_input_password_create.dart
    │   │   ├── custom_input_email.dart
    │   │   ├── custom_input_number.dart
    │   │   ├── custom_input_dropdown.dart
    │   │   └── custom_input_date.dart
    │   ├── bars/                      
    │   │   ├── custom_app_bar.dart (Base Superior)
    │   │   ├── custom_app_bar_search.dart
    │   │   ├── custom_app_bar_profile.dart
    │   │   ├── custom_bottom_app_bar.dart (Base Inferior con Notch para FAB)
    │   │   ├── custom_bottom_app_bar_item.dart
    │   │   └── custom_bottom_nav_bar_floating.dart
    │   ├── speed_dial/                
    │   │   ├── custom_speed_dial.dart (Base Vertical)
    │   │   ├── custom_speed_dial_item.dart
    │   │   ├── custom_speed_dial_radial.dart
    │   │   └── custom_speed_dial_horizontal.dart
    │   ├── grids/                     
    │   │   ├── custom_grid.dart (Base)
    │   │   ├── custom_grid_media.dart
    │   │   ├── custom_grid_stats.dart
    │   │   ├── custom_grid_matrix.dart
    │   │   └── custom_grid_product.dart
    │   ├── dismissible/               
    │   │   ├── custom_dismissible.dart (Base)
    │   │   ├── custom_dismissible_card.dart
    │   │   └── custom_dismissible_background.dart
    │   ├── dialogs/                   
    │   │   ├── custom_dialog.dart (Base)
    │   │   ├── custom_dialog_confirmation.dart
    │   │   ├── custom_dialog_danger.dart
    │   │   ├── custom_dialog_success.dart
    │   │   ├── custom_dialog_warning.dart
    │   │   ├── custom_dialog_input.dart
    │   │   ├── custom_dialog_loading.dart
    │   │   └── custom_dialog_info.dart
    │   ├── loaders/                   
    │   │   ├── custom_spinner.dart    
    │   │   ├── custom_skeleton.dart
    │   │   ├── custom_loader_dots.dart
    │   │   ├── custom_loader_linear.dart
    │   │   ├── custom_loader_typing.dart
    │   │   ├── custom_loader_wave.dart
    │   │   ├── custom_loader_pulse.dart
    │   │   └── custom_loader_overlay.dart
    ├── utils/                         
    │   ├── formatters/                
    │   │   └── date_formatter.dart    
    │   ├── validators/                
    │   │   └── form_validators.dart   
    │   └── extensions/                
    │       └── string_extension.dart  
    ├── animation/                     
    │   ├── custom_animation.dart (Base & Exporter)
    │   ├── transitions/
    │   │   └── custom_transition.dart
    │   ├── warnings/
    │   │   └── custom_warning.dart
    │   ├── status/
    │   │   └── custom_status.dart
    │   └── interactions/
    │       └── custom_interaction.dart
    └── models/                        
        └── base_response_model.dart   
```

## Detalle de Capas

### 1. Componentes Visuales (`widgets/`)
Elementos de interfaz gráfica universales que actúan como "widgets padre". Los módulos instancian estos componentes base para asegurar que toda la app se vea igual.
- **`bars/`**: Barras de navegación superior e inferior con `CustomAppBar` (base con subtítulos), `CustomSearchAppBar` (búsqueda integrada), `CustomProfileAppBar` (saludo de usuario con avatar) y `CustomBottomAppBar` con muesca/Notch (`CircularNotchedRectangle`) para encaje elegante de FABs y `CustomFloatingBottomBar` (isla flotante).
- **`speed_dial/`**: Botones flotantes expandibles (Speed Dial / Expandable FAB / Radial Menu) con `CustomSpeedDial` (vertical con oscurecimiento Backdrop Modal Barrier), `CustomRadialSpeedDial` (despliegue en abanico circular) y `CustomHorizontalSpeedDial`.
- **`grids/`**: Cuadrículas modulares responsivas con `CustomGrid` como base, galerías multimedia (`CustomMediaGrid`), dashboards de métricas (`CustomStatsGrid`), matrices de accesos rápidos (`CustomMatrixGrid`), catálogos (`CustomProductGrid`) y modificador `.cuadricula()` para listas.
- **`dismissible/`**: Envoltorios de deslizamiento táctil (Swipe-to-dismiss) con `CustomDismissible` como base, `CustomDismissibleCard`, fondos preconfigurados estilo Gmail/iOS (`CustomDismissibleBackground`) y modificador `.deslizable()` para el UI Engine.
- **`dialogs/`**: Ventanas modulares emergentes de alerta con `CustomDialog` como base y abstracciones (`CustomConfirmationDialog`, `CustomDangerDialog`, `CustomSuccessDialog`, `CustomWarningDialog`, `CustomInputDialog`, `CustomLoadingDialog`, `CustomInfoDialog`).
- **`cards/`**: Tarjetas modulares de información con `CustomCard` como base y abstracciones (`CustomProductCard`, `CustomStatCard`, `CustomProfileCard`, `CustomBannerCard`, `CustomMediaCard`, `CustomActionCard`, `CustomInfoCard`).
- **`buttons/`**: Botones estandarizados, con `CustomButton` como base y abstracciones (`CustomPrimaryButton`, `CustomSecondaryButton`, `CustomOutlineButton`, `CustomTextButton`, `CustomDangerButton`, `CustomIconButton`).
- **`pickers/`**: Componentes modulares para seleccionar datos complejos.
  - `custom_date_range_picker.dart`: Selector de rangos de fechas (Desktop & Mobile).
  - `custom_time_picker.dart`: Selector de horas en formato reloj o rueda (Desktop & Mobile).
  - `custom_media_picker.dart`: Botones integrados con el SO para seleccionar imágenes, videos o documentos de la galería/archivos.
- **`avatars/`**: Componentes para mostrar representaciones de usuario.
  - `custom_avatar.dart`: Foto de perfil circular con iniciales automáticas, distintos tamaños y sistema de estado visual (online, busy, etc.).
- **`viewers/`**: Envoltorios para interactuar con contenido.
  - `custom_interactive_viewer.dart`: Otorga capacidades de "Pinch to zoom" y arrastre sobre imágenes o contenido complejo.
- **`switches/`**: Interruptores nativos y adaptables con `CustomSwitch` como base y abstracciones (`CustomSwitchTile`, `CustomSwitchCard`, `CustomIconSwitch`, `CustomAsyncSwitch`).
- **`sliders/`**: Barras deslizables continuas y discretas con `CustomSlider` como base y abstracciones (`CustomRangeSlider`, `CustomIconSlider`, `CustomDiscreteSlider`, `CustomSliderCard`).
- **`loaders/`**: Colección exhaustiva de indicadores de carga modulares. 
  - `custom_spinner.dart`: Rueda giratoria estándar.
  - `custom_loader_dots.dart`: Puntos animados saltando en cascada.
  - `custom_loader_linear.dart`: Barra de progreso lineal.
  - `custom_loader_wave.dart`: Barras verticales saltando (estilo ecualizador).
  - `custom_loader_pulse.dart`: Efecto radar que se expande desde el centro.
  - `custom_loader_typing.dart`: Burbuja de chat con indicación de "Escribiendo...".
  - `custom_loader_overlay.dart`: Contenedor semitransparente para bloquear pantalla completa durante cargas.
  - `custom_skeleton.dart`: Esqueletos de carga modernos con abstracciones pre-armadas (`.card()`, `.listTile()`, `.profile()`, `.paragraph()`).

### 2. Herramientas y Utilidades (`utils/`)
Funciones de apoyo genéricas (utilidades padre). Todo módulo puede llamarlas para no reinventar la rueda.
- **`formatters/`**: Clases o funciones puras para dar formato a datos, como fechas o monedas (`date_formatter.dart`).
- **`validators/`**: Lógica de validación centralizada, por ejemplo para validar correos, contraseñas o números de teléfono (`form_validators.dart`).
- **`extensions/`**: Extensiones de Dart sobre tipos nativos (`String`, `DateTime`, `BuildContext`, etc.) para agregar funcionalidades convenientes y reducir código repetitivo (`string_extension.dart`).

### 3. Sistema de Animación (`animation/`)
Animaciones fluidas centralizadas basadas en `flutter_animate` aplicables mediante extensiones a cualquier Widget. Separadas en módulos temáticos pero exportadas desde un solo archivo (`custom_animation.dart`) para facilitar su uso.
- **`transitions/`**: Animaciones de entrada y salida (`.animarEntrada()`, `.animarSalida()`, `.animarRebote()`).
- **`warnings/`**: Feedback visual de alerta (`.animarError()`, `.animarLatido()`, `.animarDestelloPeligro()`).
- **`status/`**: Estados de carga y éxito (`.animarCarga()`, `.animarExito()`).
- **`interactions/`**: Respuesta a eventos táctiles (`.animarFoco()`, `.animarPresion()`).

### 4. Modelos Compartidos (`models/` - Opcional)
Modelos de datos base ("modelos padre"). Los modelos de los módulos pueden extender de estos para heredar propiedades comunes.
- **`base_response_model.dart`**: Modelos base para la estructura de respuesta genérica de la API.
