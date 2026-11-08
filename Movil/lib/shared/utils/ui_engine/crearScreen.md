# Cómo crear una Pantalla con el UI Engine

Gracias a nuestra abstracción, construir pantallas complejas toma una fracción del tiempo habitual y el código resultante es completamente semántico y fácil de leer.

Sigue estos pasos para crear una pantalla desde cero.

---

## 1. Importaciones Necesarias

En tu archivo de la nueva vista (ej. `mi_pantalla.dart`), importa el motor. Siempre necesitarás importar estos archivos:

```dart
import 'package:flutter/material.dart';

// Importa el Core del motor
import '../../shared/utils/ui_engine/ui_screen.dart';

// Importa los modificadores
import '../../shared/utils/ui_engine/widget_modifiers.dart';
import '../../shared/utils/ui_engine/list_modifiers.dart';
import '../../shared/utils/ui_engine/string_modifiers.dart';
import '../../shared/utils/ui_engine/icon_modifiers.dart';

// Importa el factory de UI (Tus inputs, botones, etc)
import '../../shared/utils/ui_engine/ui.dart';
```

*(Nota: Ajusta los `../../` dependiendo de qué tan profundo esté tu archivo en la carpeta `modules`)*

---

## 2. Definir la Pantalla como un Lienzo Unificado

Crea una clase que extienda de `UIScreen`. Pasa todas las configuraciones del andamiaje directamente a través del constructor `super(...)` sin necesidad de getters separados:

```dart
class MiPantalla extends UIScreen {
  MiPantalla({super.key})
      : super(
          titulo: "Nueva Pantalla", // Título en la AppBar (opcional)
          centrado: true,          // Centra el contenido en pantalla
          bgColor: Colors.white,   // Color de fondo del lienzo
          accionesAppBar: [ ... ], // Acciones en la barra superior
          floatingActionButton: CustomPrimaryButton(...),
        );

  @override
  Widget contenido(BuildContext context) => [
    // ... aquí va el contenido limpio ...
  ].columna();
}
```

O crea un lienzo instantáneo sin definir una clase usando `UI.lienzo`:

```dart
final pantalla = UI.lienzo(
  titulo: "Mi Pantalla",
  centrado: true,
  cuerpo: (context) => [
    "Hola Mundo".texto(size: 20),
  ],
);
```

---

## 3. Inyectar el Contenido (`contenido(BuildContext context)`)

En lugar del clásico `build`, sobrescribe el método `contenido`. 
El truco ninja aquí es **retornar una Lista (`[]`)** y al final encadenarle `.columna()` o `.fila()`. Esto te permite usar sintaxis declarativa limpia.

```dart
  // 2. CONSTRUIR EL CONTENIDO
  @override
  Widget contenido(BuildContext context) => [
    
    // Texto simple usando extensiones
    "¡Hola, Bienvenido!".texto(size: 24, negrita: true).padXY(0, 20),

    // Usando el dispensador UI para un Input
    UI.input("Escribe tu nombre", (valor) { 
      print("Escribió: $valor"); 
    })
    .maxAncho(400) // Se adapta en móvil, pero no crece más de 400px en Tablet
    .padXY(0, 10),

    // Un contenedor con estilo extremo usando un ícono
    Icons.star.icono(size: 40, color: Colors.orange)
      .pad(20)
      .estilo(
        circulo: true, 
        bg: Colors.white, 
        sombra: true,
        bordeColor: Colors.orange
      )
      .click(() => print("Estrella clickeada")),

    // Un par de botones usando Listas Inteligentes
    [
      UI.boton("Aceptar", () {}).w(150),
      "Cancelar".texto(color: Colors.red).pad(10).click(() {}),
    ].fila(espaciado: 20, mainAxis: MainAxisAlignment.center)
     .padXY(0, 30)

  ].columna(); // Transformamos mágicamente la lista maestra en una columna!
```

---

## 4. Trucos Avanzados

### A. Hacer diseños que se adapten a Tablet automáticamente (`.envoltura()`)
Si tienes tarjetas o varios elementos que en un teléfono deben ir uno debajo del otro, pero en una Tablet deben ir uno al lado del otro, **NO uses `.columna()` ni `.fila()`, usa `.envoltura()`**.

```dart
  [
    TarjetaInfo("Ventas", "\$1000"),
    TarjetaInfo("Gastos", "\$200"),
    TarjetaInfo("Usuarios", "45"),
  ].envoltura(espaciado: 15) // En móvil será vertical, en Tablet será horizontal automáticamente.
```

### B. Efecto Vidrio Esmerilado (Glassmorphism)
Usa el modificador `.cristal()` sobre cualquier elemento (Ideal sobre fondos con imágenes o gradientes).

```dart
  "Contenido Ultra Secreto".texto()
    .pad(20)
    .cristal(desenfoque: 15, opacidad: 0.2)
```

### C. Ocultar elementos condicionalmente
En lugar de hacer *if-else* feos dentro del árbol de widgets, usa `.ocultar(condicion)`.

```dart
  UI.loader().ocultar(!cargando) // Si no está cargando, este widget desaparece
```

### D. Empujar widgets (Traslación)
Si un widget necesita moverse unos cuantos píxeles hacia arriba o abajo sin usar paddings complicados, usa `.pos()`.

```dart
  // Empuja el botón 20 píxeles hacia arriba
  UI.boton("Subir", () {}).pos(y: -20)
```

---

## Resumen del Flujo de Trabajo
1. Heredas de `UIScreen`.
2. Sobrescribes título y configuraciones (`getters`).
3. Creas una lista `[...]`.
4. Llenas la lista usando primitivos `.texto()`, `.icono()` y elementos de `UI`.
5. Aplicas modificadores de diseño (`.estilo()`, `.pad()`, `.maxAncho()`).
6. Cierras la lista con `.columna()`. ¡Listo!
