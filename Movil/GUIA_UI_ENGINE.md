# Guía Definitiva del UI Engine 🚀

Bienvenido al sistema de diseño brutalmente declarativo y abstracto. Aquí no escribimos código "a lo Flutter clásico" lleno de anidamientos (`child`, `children`, `SizedBox`). Aquí usamos programación fluida (encadenamiento de métodos).

---

## 1. Crear una pantalla nueva desde 0

Toda pantalla debe heredar de `UIScreen`. Gracias a nuestra abstracción, ya no necesitas usar `@override Widget build` ni `@override Widget contenido`. Todo se inyecta directamente en el constructor usando `cuerpo: (context) => [ ... ]`.

```dart
import 'package:flutter/material.dart';
import '../../../../shared/utils/ui_engine/ui_screen.dart';
import '../../../../shared/utils/ui_engine/widget_modifiers.dart';
import '../../../../shared/utils/ui_engine/list_modifiers.dart';
import '../../../../shared/utils/ui_engine/string_modifiers.dart';

class PantallaDashboard extends UIScreen {
  
  PantallaDashboard({super.key}) : super(
    titulo: "Mi Dashboard",
    centrado: true,
    paddingX: 20.0,
    
    // Aquí defines toda la interfaz visual de arriba hacia abajo
    cuerpo: (context) => [
      
      "Bienvenido al sistema".texto(size: 24, negrita: true),
      
      // Más componentes irán aquí...

    ],
  );
}
```

---

## 2. Cómo agregar componentes (Sintaxis Declarativa)

Olvida envolver las cosas. Si quieres modificar un widget, simplemente ponle un punto (`.`) al final.

### Textos
```dart
"Hola Mundo".texto(color: Colors.blue, size: 20, negrita: true)
```

### Iconos
```dart
Icons.home.icono(size: 30, color: Colors.green)
```

### Padding y Márgenes
```dart
MiWidget().pad(16)            // Padding en todos lados
MiWidget().padXY(20, 10)      // Padding horizontal y vertical
MiWidget().padSolo(t: 10)     // Padding solo arriba (top)
```

### Filas y Columnas
Agrupa elementos en una lista `[ ]` y termínalo con `.columna()` o `.fila()`.

```dart
[
  "Elemento 1".texto(),
  "Elemento 2".texto(),
].columna(espaciado: 10, crossAxis: CrossAxisAlignment.start)
```

---

## 3. Objetos Lógicos y Conexión de Funciones (Controladores)

Para separar la lógica de la interfaz, crea clases (controladores o servicios) que manejen los datos. 
**Regla de oro:** Instáncialos como `static final` en tu pantalla para poder acceder a ellos desde dentro de `cuerpo:`.

```dart
// 1. Definimos la clase que hace el trabajo pesado
class GestorVentas {
  int totalVentas = 0;
  
  void registrarVenta() {
    totalVentas += 100;
  }
  
  String obtenerReporte() {
    return "\$ $totalVentas MXN";
  }
}

class PantallaVentas extends UIScreen {
  // 2. Instanciamos el objeto para consumirlo
  static final GestorVentas gestor = GestorVentas();

  PantallaVentas({super.key}) : super(
    titulo: "Ventas Diarias",
    cuerpo: (context) => [
      // Usaremos el gestor aquí abajo...
    ],
  );
}
```

---

## 4. Lógica Reactiva en la Interfaz (`CustomRebuilder`)

Como `UIScreen` es estático, la pantalla no se redibujará sola si cambias una variable. 
Para solucionar esto sin ensuciar el código, envuelve los componentes que necesiten "moverse" en un `CustomRebuilder`.

```dart
class PantallaVentas extends UIScreen {
  static final GestorVentas gestor = GestorVentas();

  PantallaVentas({super.key}) : super(
    titulo: "Ventas",
    cuerpo: (context) => [
      
      "Panel de Control".texto(negrita: true),

      // 3. Hacemos reactiva solo la parte que cambia
      CustomRebuilder(
        builder: (actualizar) => [
          
          // 4. Conectamos el botón con la función
          CustomPrimaryButton(
            text: "Cobrar Venta",
            onPressed: () {
              // ACTUALIZAR obliga a redibujar cuando cambian los datos
              actualizar(() {
                gestor.registrarVenta();
              });
            },
          ),
          
          // 5. Mostramos el resultado
          gestor.obtenerReporte().texto(size: 30, color: Colors.green),
          
        ].columna(espaciado: 20),
      ),

    ],
  );
}
```

---

## 5. Consumir APIs (Red)

Para hacer peticiones HTTP (GET, POST, etc.) simplemente importa nuestra abstracción brutal `ApiProvider`. Ya maneja tiempos de espera, errores e intercepciones de seguridad.

```dart
import '../../../../core/network/api_provider.dart';

class ServicioUsuarios {
  
  Future<void> cargarUsuarios() async {
    try {
      // Usas la instancia global 'api'
      final respuesta = await api.get('/users?page=1');
      print(respuesta);
    } catch (e) {
      print("Ocurrió un error: \$e");
    }
  }
}
```
