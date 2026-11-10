/** Fotos y notas de voz del chat: viajan como data URL dentro del mensaje (WebSocket). */

export const MAX_IMAGEN_BYTES = 8 * 1024 * 1024;
export const MAX_AUDIO_SEGUNDOS = 120;
/** Lado mayor de la foto que se comparte: suficiente para leer un diagrama */
const LADO_MAXIMO = 1600;

/**
 * ¿El texto que acompaña a la foto/audio menciona a la IA? Solo cuenta "@diag" ESCRITO:
 * sin mención, la foto o el audio son un mensaje normal y la IA no se mete.
 */
export function mencionaADiag(texto: string | undefined): boolean {
  return !!texto && /@diag\b/i.test(texto);
}

export function leerComoDataUrl(blob: Blob): Promise<string> {
  return new Promise((ok, mal) => {
    const lector = new FileReader();
    lector.onload = () => ok(String(lector.result));
    lector.onerror = () => mal(lector.error);
    lector.readAsDataURL(blob);
  });
}

/** Reduce la foto (JPEG, lado mayor 1600 px) para que viaje rápido a toda la sala. */
export async function comprimirImagen(archivo: File): Promise<{ dataUrl: string; mime: string }> {
  const original = await leerComoDataUrl(archivo);
  if (archivo.type === 'image/gif' || archivo.type === 'image/svg+xml') return { dataUrl: original, mime: archivo.type };
  try {
    const img = await new Promise<HTMLImageElement>((ok, mal) => {
      const i = new Image();
      i.onload = () => ok(i);
      i.onerror = mal;
      i.src = original;
    });
    const escala = Math.min(1, LADO_MAXIMO / Math.max(img.width, img.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(img.width * escala);
    canvas.height = Math.round(img.height * escala);
    const ctx = canvas.getContext('2d');
    if (!ctx) return { dataUrl: original, mime: archivo.type };
    ctx.fillStyle = '#fff'; // PNG con transparencia → fondo blanco (diagramas legibles)
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    const comprimida = canvas.toDataURL('image/jpeg', 0.85);
    return comprimida.length < original.length
      ? { dataUrl: comprimida, mime: 'image/jpeg' }
      : { dataUrl: original, mime: archivo.type };
  } catch {
    return { dataUrl: original, mime: archivo.type };
  }
}

/** Base64 sin el prefijo "data:...;base64," */
export function base64DeDataUrl(dataUrl: string): string {
  return dataUrl.slice(dataUrl.indexOf(',') + 1);
}
