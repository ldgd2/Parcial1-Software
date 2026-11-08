# Sistema de Inputs (Campos de Texto) - Documentación

Este directorio contiene todo el ecosistema de campos de texto de la aplicación. Al igual que los botones, existe un "Input Base" inteligente (`CustomInput`) del cual heredan todas las demás variantes específicas (Correo, Contraseña, Búsqueda, etc.).

---

## 1. Input Base: `CustomInput` (`custom_input.dart`)
Es el componente central que dibuja la caja de texto, maneja el estado de foco, los bordes, los colores del tema y las validaciones. **Rara vez deberías usarlo directamente**, a menos que necesites un campo de texto muy raro que no encaje en las otras categorías.

### 🛠️ Atributos Principales (Los que heredan casi todos los inputs)
Estos atributos están disponibles en prácticamente todas las variantes:

| Atributo | Tipo | Descripción |
| :--- | :--- | :--- |
| `label` | `String?` | El título que aparece **arriba** de la caja de texto. |
| `hint` | `String` | El texto gris que aparece **dentro** cuando está vacío (Ej. "Escribe aquí..."). |
| `controller` | `TextEditingController?` | El controlador para leer/escribir el texto programáticamente. |
| `onChanged` | `Function(String)?` | Se ejecuta cada vez que el usuario teclea una letra. |
| `validator` | `String? Function(String?)?`| Función para validar si el campo tiene errores. |
| `prefixIcon` | `IconData?` | Icono que aparece a la izquierda dentro de la caja. |
| `suffixIcon` | `Widget?` | Widget/Icono que aparece a la derecha. |
| `keyboardType`| `TextInputType` | Qué teclado nativo abrir (Texto, Números, Email, Teléfono). |
| `isPassword` | `bool` | Si es true, oculta el texto (***) y muestra un botón de "ojito". |
| `readOnly` | `bool` | Si es true, no despliega teclado pero se puede tocar. |
| `errorText` | `String?` | Si le pasas un texto, la caja se vuelve roja (modo error). |

---

## 2. Catálogo de Inputs Específicos (Los que debes usar)

Estas son las clases que te facilitan la vida. Ya traen los iconos correctos, los validadores preconfigurados y los teclados nativos listos para usar.

### 📧 `CustomEmailInput` (`custom_input_email.dart`)
**Propósito:** Para recolectar correos electrónicos (Login, Registro, etc.).
* **Características:** Abre el teclado nativo con el arroba (`@`) de acceso rápido y tiene el icono de sobre (✉️) por defecto.
* **Atributos Extra:** `isRequired` (bool).
* **Validación Automática:** Si `isRequired` es `true`, valida automáticamente que no esté vacío y que tenga un formato válido (`usuario@correo.com`).

**Ejemplo de uso:**
```dart
CustomEmailInput(
  controller: emailController,
  label: 'Correo Electrónico',
  hint: 'tucorreo@ejemplo.com',
  // Ya no necesitas validar manualmente la estructura del correo
)
```

---

### 🔒 `CustomPasswordInput` (`custom_input_password.dart`)
**Propósito:** Para iniciar sesión o campos donde se oculta el texto.
* **Características:** Oculta el texto por defecto (****) y muestra un icono de un "ojito" a la derecha para revelar la contraseña.
* **Implementación:** Solo lo declaras y él maneja el estado de mostrar/ocultar por sí solo.

**Ejemplo de uso:**
```dart
CustomPasswordInput(
  controller: passController,
  label: 'Contraseña',
  hint: 'Ingresa tu contraseña',
)
```

*(Nota: Existe también `CustomPasswordCreateInput` que se usa específicamente para pantallas de registro, y suele traer reglas visuales como "Debe tener 8 caracteres, 1 mayúscula...").*

---

### 🔍 `CustomSearchInput` (`custom_input_search.dart`)
**Propósito:** Barras de búsqueda.
* **Características:** Trae la lupita a la izquierda.
* **Inteligencia:** Si el usuario escribe algo, automáticamente aparece una "X" a la derecha. Si tocas la "X", el campo se limpia solo.

**Ejemplo de uso:**
```dart
CustomSearchInput(
  hint: 'Buscar productos, tiendas...',
  onChanged: (texto) {
    // Filtrar tu lista aquí
  },
)
```

---

### 🔢 `CustomNumberInput` (`custom_input_number.dart`) & `CustomCurrencyInput` (`custom_input_currency.dart`)
**Propósito:** Recolectar cantidades enteras (Number) o dinero (Currency).
* **Características:** Abren el teclado puramente numérico del celular.
* **Atributos Extra:** El de Currency suele autocompletar el signo `$` y formatear los miles (ej. `$1,500.00`).

**Ejemplo de uso:**
```dart
CustomCurrencyInput(
  label: 'Monto a transferir',
  onChanged: (valor) { ... },
)
```

---

### 📅 `CustomDateInput` (`custom_input_date.dart`)
**Propósito:** Seleccionar fechas (Cumpleaños, Reservas).
* **Características:** Es de solo lectura (`readOnly = true`). En lugar de abrir el teclado de letras, cuando lo tocas (`onTap`) debería lanzar un calendario (Date Picker).

**Ejemplo de uso:**
```dart
CustomDateInput(
  label: 'Fecha de Nacimiento',
  hint: 'DD/MM/AAAA',
  controller: dateController, // Guardas la fecha aquí cuando la elijan
)
```

---

### 📝 `CustomTextareaInput` (`custom_input_textarea.dart`)
**Propósito:** Campos de texto largos (Comentarios, Biografías, Direcciones exactas).
* **Características:** A diferencia de los inputs normales de 1 sola línea, este abarca más espacio vertical.
* **Atributos Extra:** `maxLines` suele estar en `3` o `5` por defecto.

**Ejemplo de uso:**
```dart
CustomTextareaInput(
  label: 'Comentarios Adicionales',
  hint: 'Escribe aquí cualquier detalle extra...',
  maxLines: 4,
)
```

---

### 📱 `CustomPhoneInput` (`custom_input_phone.dart`)
**Propósito:** Recolectar números de celular.
* **Características:** Muestra icono de teléfono, abre el teclado de marcación (Dialpad) e incluye validación de longitud máxima (usualmente 10 dígitos).

**Ejemplo de uso:**
```dart
CustomPhoneInput(
  label: 'Número de Celular',
  hint: 'Ej. 55 1234 5678',
)
```

---

### 🔽 `CustomDropdownInput` (`custom_input_dropdown.dart`)
**Propósito:** Un menú desplegable (Select) que visualmente parece una caja de texto idéntica al resto.
* **Atributos Extra:** `options` (Mapa clave-valor abstracto), `value` (Valor actual) y soporte para `controller`.
* **Abstracción Total:** No tienes que construir `DropdownMenuItem` manualmente. Le pasas un simple diccionario (Map) y él hace el resto. Además, **puedes pasarle un `TextEditingController`** al igual que a los demás inputs, y él guardará la selección allí como texto automáticamente.

**Ejemplo de uso:**
```dart
CustomDropdownInput(
  label: 'Género',
  hint: 'Selecciona tu género',
  controller: generoController, // ¡Funciona igual que los text inputs!
  options: const {
    'M': 'Masculino',
    'F': 'Femenino',
    'O': 'Otro',
  },
  // onChange es opcional si ya usas controller, 
  // pero sigue estando disponible si necesitas reaccionar al cambio.
)
```
