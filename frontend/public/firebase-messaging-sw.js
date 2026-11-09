/* CU39: service worker de Firebase Cloud Messaging.
   Muestra los avisos cuando la app está cerrada o en segundo plano.
   La configuración (pública) llega en la URL de registro: ?config=<json>&v=<versión del SDK>. */
const params = new URL(self.location.href).searchParams;
const version = params.get('v') || '10.12.2';

importScripts(
  `https://www.gstatic.com/firebasejs/${version}/firebase-app-compat.js`,
  `https://www.gstatic.com/firebasejs/${version}/firebase-messaging-compat.js`
);

try {
  firebase.initializeApp(JSON.parse(params.get('config') || '{}'));
  // Los mensajes con "notification" los muestra el SDK solo; el clic abre el enlace (webpush.fcm_options.link).
  firebase.messaging();
} catch (e) {
  console.warn('[firebase-messaging-sw] configuración inválida', e);
}
