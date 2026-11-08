# Sistema de Botones - Documentación

Este directorio contiene el sistema centralizado de botones de la aplicación. Todos los botones se basan en una estructura base inteligente (`CustomButton`) que maneja estados, estilos y cargas asíncronas automáticamente.

---

## 1. Botón Base: `CustomButton` (`custom_button.dart`)
Es el "motor" principal. Por lo general, **no lo llamas directamente en las pantallas**, sino que usas sus variantes (Primario, Secundario, etc.). Sin embargo, si necesitas un botón totalmente ajeno a tu sistema de diseño, puedes usarlo.

### 🧠 Inteligencia Asíncrona
Si le pasas a `onPressed` una función asíncrona (`async`), el botón detecta el `Future`, muestra un indicador de carga (`CircularProgressIndicator`), y se deshabilita automáticamente para evitar clics duplicados hasta que la tarea termine.

### 🛠️ Atributos Principales
* **`text`** (`String?`): Texto a mostrar en el botón.
* **`onPressed`** (`FutureOr<void> Function()?`): Acción a ejecutar (síncrona o asíncrona).
* **`icon`** (`IconData?`): Icono a la izquierda del texto.
* **`suffixIcon`** (`IconData?`): Icono a la derecha del texto.
* **`customChild`** (`Widget?`): Reemplaza todo el contenido interno (texto/iconos) por tu propio diseño.
* **`isLoading`** (`bool`): Fuerzas el estado de carga manualmente. Default: `false`.
* **`isDisabled`** (`bool`): Deshabilita el botón visual y funcionalmente. Default: `false`.
* **`isFullWidth`** (`bool`): Expande el botón al 100% del ancho de su contenedor padre. Default: `false`.
* **`width` / `height`** (`double?`): Dimensiones específicas en píxeles.
* **`backgroundColor` / `textColor` / `borderColor`**: Para forzar colores ignorando el tema global.

### 📝 Ejemplo de Uso (CustomButton puro)
```dart
CustomButton(
  text: 'Botón Súper Personalizado',
  backgroundColor: Colors.purple,
  textColor: Colors.yellow,
  onPressed: () async {
    // Al esperar un Future, el botón se bloquea y muestra un spinner
    await Future.delayed(const Duration(seconds: 2));
  },
)
```

---

## 2. Variantes (Los que debes usar en UI)
Estas clases heredan todos los atributos de `CustomButton` y simplemente pre-configuran colores, bordes o elevaciones según las reglas de negocio. **Son los que realmente usas al programar pantallas.**

### 🔹 `CustomPrimaryButton` (`custom_button_primary.dart`)
**Propósito:** La acción número uno de la pantalla (Guardar, Enviar, Pagar, Iniciar Sesión). Es el que más resalta, rellenado con el color primario.

**Ejemplo de implementación:**
```dart
CustomPrimaryButton(
  text: 'Iniciar Sesión',
  icon: Icons.login, // Opcional
  isFullWidth: true, // Ideal para la parte baja de una pantalla
  onPressed: () async {
    await login(); 
  },
)
```

### 🔹 `CustomSecondaryButton` (`custom_button_secondary.dart`)
**Propósito:** Acciones alternativas que no son las más importantes (Opciones avanzadas, Compartir). Usa el color secundario como relleno.

**Ejemplo de implementación:**
```dart
CustomSecondaryButton(
  text: 'Filtros Avanzados',
  icon: Icons.filter_list,
  onPressed: () {
    mostrarFiltros(context);
  },
)
```

### 🔹 `CustomButtonOutline` (`custom_button_outline.dart`)
**Propósito:** Acciones de cancelación o secundarias. No tiene color de fondo sólido, solo un contorno del color primario. Mantiene el peso visual ligero.

**Ejemplo de implementación:**
```dart
CustomButtonOutline(
  text: 'Cancelar',
  onPressed: () => Navigator.pop(context),
)
```

### 🔹 `CustomButtonText` (`custom_button_text.dart`)
**Propósito:** Acciones terciarias, luce como un enlace. Ideal para acciones que no quieres que distraigan (Olvidé mi contraseña, Saltar tutorial).

**Ejemplo de implementación:**
```dart
CustomButtonText(
  text: 'Saltar este paso por ahora',
  onPressed: () => irAlInicio(),
)
```

### 🔹 `CustomButtonDanger` (`custom_button_danger.dart`)
**Propósito:** Acciones destructivas e irreversibles (Eliminar cuenta, Cerrar sesión, Borrar elemento). Rellenado con rojo (color de error).

**Ejemplo de implementación:**
```dart
CustomButtonDanger(
  text: 'Eliminar Proyecto',
  icon: Icons.warning_rounded,
  onPressed: () async {
    await api.deleteProject(id);
  },
)
```

### 🔹 `CustomButtonIcon` (`custom_button_icon.dart`)
**Propósito:** Botones pequeños y compactos que solo muestran un icono, sin texto (Buscador, Menú hamburguesa, Favorito). 

**Atributos específicos obligatorios:**
* **`icon`**: Requiere el icono (no es opcional como en el resto).

**Ejemplo de implementación:**
```dart
CustomButtonIcon(
  icon: Icons.favorite_border,
  onPressed: () {
    marcarComoFavorito();
  },
)
```

---

## 3. Agrupador de Botones (`custom_button_group.dart`)
**Propósito:** Agrupar varios botones manteniendo un espaciado consistente. Abstrae la necesidad de escribir manualmente `Row`, `Column`, `Expanded` o `SizedBox`.

### 🛠️ Atributos de `CustomButtonGroup`
* **`buttons`** (`List<Widget>`): Lista de widgets (Tus botones).
* **`direction`** (`Axis`): `Axis.horizontal` (lado a lado) o `Axis.vertical` (arriba a abajo). **Default: `Axis.horizontal`**.
* **`spacing`** (`double`): Píxeles de separación entre los botones. **Default: `16.0`**.
* **`expandButtons`** (`bool`): 
  * En horizontal: Convierte a todos en `Expanded` (mismo ancho).
  * En vertical: Les asigna un ancho del 100%. 
  * **Default: `true`**.

### 📝 Ejemplo: Fila Horizontal (Cancelar y Aceptar de igual tamaño)
```dart
CustomButtonGroup(
  direction: Axis.horizontal, 
  spacing: 16.0,
  buttons: [
    CustomButtonOutline(
      text: 'Cancelar', 
      onPressed: () => Navigator.pop(context),
    ),
    CustomPrimaryButton(
      text: 'Confirmar', 
      onPressed: () async {
        await guardarDatos();
      },
    ),
  ],
)
```

### 📝 Ejemplo: Columna Vertical (Botones anchos)
```dart
CustomButtonGroup(
  direction: Axis.vertical, 
  spacing: 12.0, // Un poco menos de espacio que en horizontal suele verse bien
  buttons: [
    CustomPrimaryButton(
      text: 'Continuar al Pago', 
      onPressed: () { ... }
    ),
    CustomButtonText(
      text: 'Seguir comprando', 
      onPressed: () { ... }
    ),
  ],
)
```
