# Pendientes

## App móvil (`Movil/`), para revisar con el líder

El líder ya probó las notificaciones push del móvil y funcionan. Esto quedó anotado en la revisión del 2026-11-10 y **no se cambió**:

- [ ] **Cerrar sesión no quita el celular.** `AuthController.cerrarSesion()` no borra el registro del celular (`DELETE /api/notificaciones/dispositivos?token=...`). Por eso el celular sigue recibiendo los avisos de esa cuenta hasta que otra cuenta inicie sesión en él. En la web sí se quita al salir.
- [ ] **`google-services.json` está subido y también ignorado.** El archivo está en el repo, pero `Movil/.gitignore` lo ignora. No es secreto y hace falta para compilar Android, así que conviene quitar esas líneas del `.gitignore` (o dejar de subirlo y explicar cómo conseguirlo).
- [ ] **El permiso de notificaciones frena el arranque.** `main.dart` espera a `PushNotificationService.inicializar()` antes de `runApp`, así que la app no abre hasta que el usuario responde al pedido de permiso. Se podría pedir después de abrir la app.
- [ ] **La URL del servidor ya no se puede cambiar.** Se quitó la opción del login (`LocalStorageService.setBaseUrl` ahora no hace nada) y la app solo usa `API_BASE_URL` del `.env`. Hay que confirmar si fue a propósito.
- [ ] **Versión de Flutter.** `pubspec.yaml` pide Dart `^3.11.0`, que viene con Flutter 3.47 o más nuevo. Con Flutter 3.38 (Dart 3.10) no corre `flutter pub get` y no se puede compilar ni analizar.
